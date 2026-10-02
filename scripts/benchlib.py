"""Portable source and archive guards; Python standard library only."""
from __future__ import annotations
import contextlib, errno, hashlib, json, os, shutil, tarfile, tempfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def records(root):
    root = Path(root)
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError(f'Symlinks are not allowed in frozen inputs: {root}')
    return {p.relative_to(root).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def hashes(root):
    return {k: v['sha256'] for k,v in records(root).items()}

def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def safe_relative(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError(f'Unsafe relative path: {value!r}')
    return path

def bundled_manifest(repo=REPO):
    repo = Path(repo)
    manifest = json.loads((repo/'vendor/manifest.json').read_text())
    if manifest.get('schema') != 1 or not manifest.get('complete'):
        raise ValueError('Incomplete bundled source manifest')
    observed = {}
    for name in ('vendor', 'assets'):
        observed.update({name+'/'+k: v for k,v in records(repo/name).items()
                         if name+'/'+k != 'vendor/manifest.json'})
    if observed != manifest['files']:
        changed = sorted(k for k in set(observed)|set(manifest['files']) if observed.get(k)!=manifest['files'].get(k))
        raise ValueError(f'Bundled inputs differ from pinned manifest: {changed[:12]}')
    return manifest

class ArchiveStore:
    """Verify untouched campaign archives and resolve historical absolute paths."""
    def __init__(self, repo=REPO, index=None):
        self.repo = Path(repo).resolve()
        self.index = Path(index or self.repo/'results/index.json')
        data = json.loads(self.index.read_text())
        if data.get('schema') != 1:
            raise ValueError('Unknown archive-index schema')
        self.campaigns = data['campaigns']
        self.materialized = {}

    def campaign(self, label):
        matches = [c for c in self.campaigns if c['label']==label]
        if len(matches)!=1: raise ValueError(f'Unknown/duplicate campaign: {label}')
        return matches[0]

    def original(self, path):
        raw = str(path)
        matches = [c for c in self.campaigns if raw==c['original_root'] or raw.startswith(c['original_root'].rstrip('/')+'/')]
        if not matches: raise ValueError(f'Historical path is not archived: {raw}')
        entry = max(matches, key=lambda c: len(c['original_root']))
        relative = raw[len(entry['original_root']):].lstrip('/')
        if relative: safe_relative(relative)
        return entry, relative

    def inspect(self, label, destination=None, metadata_only=False):
        """One streaming pass verifies every retained byte; optional safe extraction."""
        campaign = self.campaign(label)
        safe_relative(campaign['path'])
        directory = self.repo/campaign['path']
        manifest = json.loads((directory/'archive.json').read_text())
        if not manifest.get('complete') or manifest['schema']!=1 or manifest['label']!=label or manifest['original_root']!=campaign['original_root']:
            raise ValueError(f'Invalid archive manifest: {label}')
        for key in ('sha256','bytes'):
            if campaign['archive'][key] != manifest['archive'][key]: raise ValueError(f'Index/archive disagreement: {label}/{key}')
        safe_relative(manifest['archive']['path'])
        archive = directory/manifest['archive']['path']
        if archive.stat().st_size!=manifest['archive']['bytes'] or sha(archive)!=manifest['archive']['sha256']:
            raise ValueError(f'Compressed archive checksum mismatch: {label}')
        destination = Path(destination).resolve() if destination is not None else None
        if destination is not None:
            if destination.exists(): raise ValueError(f'Archive destination exists: {destination}')
            destination.mkdir(parents=True)
        metadata_suffixes={'.json','.csv','.py','.stdout','.stderr','.log','.txt','.md','.lock','.diff'}
        def keep(relative):
            return destination is not None and (not metadata_only or Path(relative).suffix in metadata_suffixes)
        def content_key(record):return record['sha256'],record['bytes']
        # A .json alias can refer to an earlier .bin canonical member that the
        # extension filter would otherwise discard. Retain only needed groups,
        # on disk, while streaming the canonical bytes once.
        for relative,record in manifest['files'].items():
            safe_relative(relative)
            checksum=record.get('sha256');size=record.get('bytes')
            if not isinstance(checksum,str) or len(checksum)!=64 or any(ch not in '0123456789abcdef' for ch in checksum) or not isinstance(size,int) or isinstance(size,bool) or size<0:
                raise ValueError(f'Invalid retained-file record: {relative}')
        needed={content_key(record) for relative,record in manifest['files'].items() if keep(relative)}
        observed={};regular_names=set();blobs={}
        with contextlib.ExitStack() as lifetime:
            cache=None
            if destination is not None:
                cache=Path(lifetime.enter_context(tempfile.TemporaryDirectory(prefix='.content-',dir=destination.parent)))
            stream=lifetime.enter_context(tarfile.open(archive, 'r|gz'))
            for member in stream:
                prefix=label+'/'
                if not member.name.startswith(prefix) or not (member.isfile() or member.islnk()):raise ValueError(f'Unexpected tar member: {member.name}')
                relative=member.name[len(prefix):];safe_relative(relative)
                if relative in observed or relative not in manifest['files']:raise ValueError(f'Unexpected/duplicate tar member: {member.name}')
                expected=manifest['files'][relative];key=content_key(expected)
                if member.islnk():
                    if member.size!=0 or not member.linkname.startswith(prefix):raise ValueError(f'Unsafe hardlink target: {member.name} -> {member.linkname}')
                    target=member.linkname[len(prefix):];safe_relative(target)
                    # Only prior regular members are canonical. No forward
                    # links, link chains, other campaigns or symlinks.
                    if target not in regular_names:raise ValueError(f'Hardlink target must be a prior regular member: {member.name} -> {member.linkname}')
                    if observed[target]!=expected:raise ValueError(f'Hardlink content differs from retained-file record: {member.name}')
                    observed[relative]=dict(observed[target])
                else:
                    if member.size!=expected['bytes']:raise ValueError(f'Tar member size differs: {member.name}')
                    output=None;blob=None
                    if key in needed and key not in blobs:
                        blob=cache/(expected['sha256']+'-'+str(expected['bytes']));output=blob.open('xb')
                    digest=hashlib.sha256();size=0
                    try:
                        with stream.extractfile(member) as source:
                            while chunk:=source.read(1024*1024):
                                digest.update(chunk);size+=len(chunk)
                                if output is not None:output.write(chunk)
                    finally:
                        if output is not None:output.close()
                    observed[relative]={'sha256':digest.hexdigest(),'bytes':size}
                    if observed[relative]!=expected:raise ValueError(f'Tar member checksum differs: {member.name}')
                    regular_names.add(relative)
                    if blob is not None:blobs[key]=blob
                if keep(relative):
                    if key not in blobs:raise ValueError(f'Needed canonical content unavailable: {member.name}')
                    path=destination/relative;path.parent.mkdir(parents=True,exist_ok=True)
                    try:os.link(blobs[key],path)
                    except OSError as error:
                        if error.errno not in (errno.EXDEV,errno.EPERM,errno.ENOTSUP):raise
                        with blobs[key].open('rb') as source,path.open('xb') as output:shutil.copyfileobj(source,output)
        if observed!=manifest['files']: raise ValueError(f'Missing tar members: {label}')
        if destination is not None:self.materialized[label]=destination
        return {'label':label,'files_verified':len(observed),'raw_bytes':sum(v['bytes'] for v in observed.values()),'omitted_files':len(manifest['omitted'])}

    def mapped(self, original):
        campaign,relative=self.original(original)
        destination=self.materialized.get(campaign['label'])
        if destination is None: raise ValueError(f'Campaign has not been materialized: {campaign["label"]}')
        path=destination/relative
        if not path.exists(): raise ValueError(f'Path omitted/not materialized: {original}')
        return path

    def path_map(self):
        return {c['original_root']:str(self.materialized[c['label']]) for c in self.campaigns if c['label'] in self.materialized}

def read_path_map(path):
    mapping=json.loads(Path(path).read_text()) if path else {}
    def resolve(value):
        raw=str(value)
        matches=[original for original in mapping if raw==original or raw.startswith(original.rstrip('/')+'/')]
        if not matches:
            if mapping:
                if any(raw==local or raw.startswith(local.rstrip('/')+'/') for local in mapping.values()):return Path(value)
                raise ValueError(f'Path has no verified archive mapping: {raw}')
            return Path(value)
        root=max(matches,key=len)
        relative=raw[len(root):].lstrip('/')
        if relative:safe_relative(relative)
        return Path(mapping[root])/relative
    return resolve
