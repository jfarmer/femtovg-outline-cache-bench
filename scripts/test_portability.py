#!/usr/bin/env python3
"""Small synthetic checks of source, path, relocation and archive guards."""
import hashlib,importlib.util,io,json,sys,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import benchlib

def module(name):
    spec=importlib.util.spec_from_file_location('test_'+name,Path(__file__).with_name(name+'.py'));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def manifest(repo):
    files={}
    for folder in ('vendor','assets'):files.update({folder+'/'+k:v for k,v in benchlib.records(repo/folder).items() if folder+'/'+k!='vendor/manifest.json'})
    benchlib.write_json(repo/'vendor/manifest.json',{'schema':1,'complete':True,'pins':{'femtovg_master':'pinned-master','femtovg_current':'pinned-current','alustin':'pinned-app'},'versions':['master','current','final','route'],'files':files})

class Guards(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='outline-portable-smoke-',dir='/private/tmp');self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_source_checksum_and_unexpected_file(self):
        repo=self.root/'repo';(repo/'vendor').mkdir(parents=True);(repo/'assets').mkdir();(repo/'vendor/pinned.rs').write_text('pinned source');manifest(repo)
        benchlib.bundled_manifest(repo)
        (repo/'vendor/pinned.rs').write_text('changed source')
        with self.assertRaisesRegex(ValueError,'differ'):benchlib.bundled_manifest(repo)
        (repo/'vendor/pinned.rs').write_text('pinned source');(repo/'assets/unrecorded.ttf').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError,'differ'):benchlib.bundled_manifest(repo)
    def archive(self,repo,label,original,contents):
        directory=repo/'results'/label;directory.mkdir(parents=True);archive=directory/'records.tar.gz';files={}
        with tarfile.open(archive,'w:gz') as output:
            for relative,data in contents.items():
                entry=tarfile.TarInfo(label+'/'+relative);entry.size=len(data);output.addfile(entry,io.BytesIO(data));files[relative]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
        record={'path':'records.tar.gz','sha256':benchlib.sha(archive),'bytes':archive.stat().st_size}
        benchlib.write_json(directory/'archive.json',{'schema':1,'complete':True,'label':label,'original_root':original,'files':files,'omitted':[],'archive':record})
        return {'label':label,'path':'results/'+label,'original_root':original,'archive':record}
    def test_longest_prefix_and_untouched_original_paths(self):
        repo=self.root/'repo';campaigns=[self.archive(repo,'outer','/old/tmp/study',{'summary.json':b'{"report":"/old/tmp/study/nested/raw.json"}'}),self.archive(repo,'inner','/old/tmp/study/nested',{'raw.json':b'{}'})]
        benchlib.write_json(repo/'results/index.json',{'schema':1,'campaigns':campaigns});store=benchlib.ArchiveStore(repo)
        for campaign in campaigns:store.inspect(campaign['label'],self.root/campaign['label'],metadata_only=True)
        self.assertEqual(store.mapped('/old/tmp/study/nested/raw.json'),self.root/'inner/raw.json')
        self.assertIn('/old/tmp/study/nested/raw.json',store.mapped('/old/tmp/study/summary.json').read_text())
        benchlib.write_json(self.root/'map.json',store.path_map());resolve=benchlib.read_path_map(self.root/'map.json')
        self.assertEqual(resolve('/old/tmp/study/nested/raw.json'),self.root/'inner/raw.json')
        self.assertEqual(resolve(self.root/'inner/raw.json'),self.root/'inner/raw.json')
        with self.assertRaisesRegex(ValueError,'no verified archive mapping'):resolve('/old/unarchived/possibly-existing.json')
    def test_archive_checksum_and_traversal_rejection(self):
        repo=self.root/'repo';campaign=self.archive(repo,'bad','/old/bad',{'../escape.json':b'{}'});benchlib.write_json(repo/'results/index.json',{'schema':1,'campaigns':[campaign]})
        with self.assertRaisesRegex(ValueError,'Unsafe'):benchlib.ArchiveStore(repo).inspect('bad',self.root/'extract')
        archive=repo/'results/bad/records.tar.gz';archive.write_bytes(archive.read_bytes()+b'tampered')
        with self.assertRaisesRegex(ValueError,'checksum'):benchlib.ArchiveStore(repo).inspect('bad')
    def hardlinked_archive(self,repo,label,items):
        directory=repo/'results'/label;directory.mkdir(parents=True);archive=directory/'records.tar.gz';files={}
        with tarfile.open(archive,'w:gz') as output:
            for relative,value in items:
                entry=tarfile.TarInfo(label+'/'+relative)
                if isinstance(value,tuple):
                    target,data=value;entry.type=tarfile.LNKTYPE;entry.linkname=target if target.startswith('/') else label+'/'+target;entry.size=0;output.addfile(entry)
                else:data=value;entry.size=len(data);output.addfile(entry,io.BytesIO(data))
                files[relative]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
        record={'path':'records.tar.gz','sha256':benchlib.sha(archive),'bytes':archive.stat().st_size}
        benchlib.write_json(directory/'archive.json',{'schema':1,'complete':True,'label':label,'original_root':'/old/'+label,'files':files,'omitted':[],'archive':record})
        campaign={'label':label,'path':'results/'+label,'original_root':'/old/'+label,'archive':record}
        benchlib.write_json(repo/'results/index.json',{'schema':1,'campaigns':[campaign]});return benchlib.ArchiveStore(repo)
    def test_hardlink_metadata_alias_keeps_excluded_canonical_bytes(self):
        payload=b'{"retained":"identical bytes, different suffixes"}\n'
        store=self.hardlinked_archive(self.root/'repo','linked',[('canonical.bin',payload),('nested/report.json',('canonical.bin',payload)),('other.stdout',('canonical.bin',payload)),('unneeded.rgba',b'pixel bytes')])
        output=self.root/'metadata';result=store.inspect('linked',output,metadata_only=True)
        self.assertEqual(result['files_verified'],4);self.assertFalse((output/'canonical.bin').exists());self.assertFalse((output/'unneeded.rgba').exists())
        self.assertEqual((output/'nested/report.json').read_bytes(),payload);self.assertEqual((output/'other.stdout').read_bytes(),payload)
        self.assertFalse(list(self.root.glob('.content-*')))
        full=self.root/'full';store.inspect('linked',full)
        self.assertEqual((full/'canonical.bin').read_bytes(),payload);self.assertEqual((full/'nested/report.json').read_bytes(),payload);self.assertEqual((full/'unneeded.rgba').read_bytes(),b'pixel bytes')
    def test_hardlink_escape_forward_chain_and_metadata_mismatch_rejected(self):
        payload=b'canonical data'
        cases=[('escape',[('canonical.bin',payload),('alias.json',('../outside.bin',payload))],'Unsafe'),
               ('absolute',[('canonical.bin',payload),('alias.json',('/outside.bin',payload))],'Unsafe hardlink'),
               ('forward',[('alias.json',('future.bin',payload)),('future.bin',payload)],'prior regular'),
               ('chain',[('canonical.bin',payload),('alias.json',('canonical.bin',payload)),('chain.json',('alias.json',payload))],'prior regular'),
               ('extent',[('canonical.bin',payload),('alias.json',('canonical.bin',payload+b'extra'))],'content differs'),
               ('checksum',[('canonical.bin',payload),('alias.json',('canonical.bin',b'x'*len(payload)))],'content differs')]
        for label,items,message in cases:
            with self.subTest(label=label):
                store=self.hardlinked_archive(self.root/label,label,items)
                with self.assertRaisesRegex(ValueError,message):store.inspect(label,self.root/(label+'-output'),metadata_only=True)
    def test_prepare_is_fresh_and_preserves_vendor(self):
        repo=self.root/'repo';core=repo/'vendor/runtime/core';app=repo/'vendor/runtime/app'
        def put(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        put(core/'runner/src/main.rs','const ASSETS: &str = "/Users/jesse/github/femtovg/examples/assets";')
        put(core/'run.py',"ASSETS=Path('/Users/jesse/github/femtovg/examples/assets')\nV=Path('/Users/jesse/github/alustin-gui-v2/crates/alustin-gui/assets/fonts/Vollkorn-Medium.ttf')\nP=Path('/private/tmp/femtovg-open-font-search/candidate-agent/PTSans-Regular.ttf')\nL=Path('/private/tmp/femtovg-liberation-font-review/liberation-fonts-ttf-2.1.5/LiberationSerif-Regular.ttf')\n")
        put(app/'baseline_run_helpers.py','ROOT=Path("/Users/jesse/github/alustin-gui-v2")\nV=ROOT / "crates/alustin-gui/assets/fonts/Vollkorn-Medium.ttf"\nR=Path("/Users/jesse/github/femtovg/examples/assets/RobotoFlex-VariableFont.ttf")\nP=Path("/private/tmp/femtovg-open-font-search/candidate-agent/PTSans-Regular.ttf")\nL=Path("/private/tmp/femtovg-liberation-font-review/liberation-fonts-ttf-2.1.5/LiberationSerif-Regular.ttf")\n')
        for path in (core/'verify_ready.py',app/'verify_ready.py'):put(path,'historical guard\n')
        put(repo/'vendor/app-inputs/input.json','{}');put(repo/'assets/font.ttf','font');put(repo/'scripts/portable_verify_ready.py','fresh guard\n');manifest(repo)
        before=benchlib.records(repo/'vendor');output=self.root/'runtime with spaces';prepare=module('prepare')
        with patch.object(prepare,'REPO',repo),patch.object(prepare,'bundled_manifest',lambda:benchlib.bundled_manifest(repo)),patch.object(sys,'argv',['prepare.py','--output',str(output)]):prepare.main()
        self.assertEqual(benchlib.records(repo/'vendor'),before)
        data=json.loads((output/'prepare-provenance.json').read_text());self.assertEqual(len(data['relocations']),12)
        self.assertIn(str(output/'assets'),(output/'core/runner/src/main.rs').read_text());self.assertEqual((output/'core/verify_ready.py').read_text(),'fresh guard\n')
        build=module('build')
        with patch.object(build,'REPO',repo),patch.object(build,'bundled_manifest',lambda:benchlib.bundled_manifest(repo)):
            build.verify_prepared(output)
            (output/'core/runner/src/main.rs').write_text('tampered')
            with self.assertRaisesRegex(ValueError,'changed'):build.verify_prepared(output)
        with patch.object(prepare,'REPO',repo),patch.object(prepare,'bundled_manifest',lambda:benchlib.bundled_manifest(repo)),patch.object(sys,'argv',['prepare.py','--output',str(output)]):
            with self.assertRaises(SystemExit):prepare.main()
    def test_every_replay_variant_builds_without_binary_reuse(self):
        build=module('build');runtime=self.root/'runtime';core=runtime/'core';runner=core/'runner';variants=['master','current','final','route']
        runner.mkdir(parents=True);(runner/'src').mkdir();(runner/'src/main.rs').write_text('fixed drawing');(runner/'Cargo.toml').write_text('path = "../replay-sources/current"\n');(runner/'Cargo.lock').write_text('pinned lock')
        frozen={};raw=b'fn fixed_renderer() {}\n'
        barriers=b''.join((b'        std::hint::black_box(images);\n',b'        std::hint::black_box(verts);\n',b'        std::hint::black_box(&commands);\n',b'        std::hint::black_box(&data);\n'))
        (core/'instrumentation').mkdir();(core/'instrumentation/void.rs').write_bytes(raw+barriers)
        for variant in variants:
            source=core/'snapshots'/variant;(source/'src/renderer').mkdir(parents=True)
            (source/'src/renderer/void.rs').write_bytes(raw);(source/'Cargo.toml').write_text('[package]\nname="femtovg"\n')
            (source/'src/lib.rs').write_text('impl Canvas {\n\n    /// Fixed '+variant+'\n    pub fn set_size(&mut self, width: u32, height: u32, dpi: f32) { }\n}\n')
            frozen[variant]={'source_files':benchlib.hashes(source)}
        benchlib.write_json(core/'snapshot-provenance.json',frozen);benchlib.write_json(runtime/'prepare-provenance.json',{'complete':True})
        calls=[]
        def fake_command(arguments,cwd=None):
            if arguments[:2]==['cargo','metadata']:return json.dumps({'packages':[{'name':'swash','version':'0.2.10'},{'name':'skrifa','version':'0.43.2'}]}).encode()
            return b'synthetic toolchain'
        def fake_build(arguments,**kwargs):
            self.assertEqual(arguments[:2],['cargo','build']);calls.append(list(arguments))
            target=Path(arguments[arguments.index('--target-dir')+1]);(target/'release').mkdir(parents=True,exist_ok=True)
            (target/'release/femtovg-example-outline-review').write_bytes((runner/'Cargo.toml').read_bytes())
        with patch.object(build,'command',fake_command),patch.object(build.subprocess,'run',fake_build):build.build_replay(runtime,{'versions':variants})
        data=json.loads((core/'replay-build-provenance.json').read_text());self.assertTrue(data['complete']);self.assertEqual(len(calls),4)
        self.assertEqual(set(data['variants']),set(variants));self.assertTrue(all(record['reused_binary'] is False for record in data['variants'].values()))
        self.assertEqual(len({record['binary_sha256'] for record in data['variants'].values()}),4)
        self.assertEqual((runner/'Cargo.toml').read_text(),'path = "../replay-sources/current"\n')
        self.assertEqual((runner/'Cargo.lock').read_text(),'pinned lock')
        with self.assertRaisesRegex(ValueError,'already exist'):build.build_replay(runtime,{'versions':variants})

if __name__=='__main__':unittest.main()
