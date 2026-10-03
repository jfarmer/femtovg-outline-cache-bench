#!/usr/bin/env python3
"""Prepare new validation/analysis drivers without editing prepared run inputs."""
import argparse, ast, hashlib, json, shutil
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def replace(path,old,new):
    code=path.read_text()
    if code.count(old)!=1:raise ValueError(f'Expected one adaptation marker in {path}: {old!r}')
    path.write_text(code.replace(old,new))

HELPER = '''"""Exact native-oracle ledger checks; no benchmark or rendering code."""
import hashlib,json
from pathlib import Path
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_ledger(path,phases,versions):
    path=Path(path);data=json.loads(path.read_text())
    if data.get('schema')!=1 or data.get('complete') is not True or data.get('versions')!=list(versions):
        raise ValueError('Incomplete or wrong-version native oracle ledger')
    if data.get('oracle_label')!='native-master-offset-oracle':raise ValueError('Wrong native oracle reference')
    proofs={}
    for kind in ('oracle_prepare','oracle_build'):
        record=data[kind];proof_path=Path(record['path'])
        if not proof_path.is_file() or sha(proof_path)!=record['sha256']:raise ValueError('Native oracle proof identity changed')
        proofs[kind]=json.loads(proof_path.read_text())
        if proofs[kind].get('complete') is not True:raise ValueError('Incomplete native oracle source/build proof')
    if proofs['oracle_prepare'].get('label')!='native-master-offset-oracle' or proofs['oracle_prepare'].get('changed_files')!=['src/text.rs']:
        raise ValueError('Native oracle must change only the master atlas phase identity')
    if proofs['oracle_build']['prepare_sha256']!=data['oracle_prepare']['sha256']:
        raise ValueError('Native oracle build does not reference this exact source proof')
    captures=data['launches']
    if len(captures)!=12 or any(row.get('complete') is not True for row in captures):raise ValueError('Incomplete native oracle/master captures')
    if {(row['font'],int(row['dpi']),row['label']) for row in captures}!={(font,dpi,label) for font in ('stock','vollkorn','ptsans') for dpi in (1,2) for label in ('master','oracle')}:
        raise ValueError('Native oracle/master capture factors differ')
    expected={(scene,phase) for scene,items in phases.items() for phase in items}
    configurations={}
    for configuration in data['configurations']:
        key=(configuration['font'],int(configuration['dpi']))
        if key in configurations:raise ValueError('Duplicate oracle font/DPR configuration')
        values={}
        for row in configuration['phases']:
            identity=(row['scene'],row['phase'])
            if identity in values or identity not in expected:raise ValueError('Duplicate/unexpected oracle phase')
            if row['frames']!=phases[identity[0]][identity[1]]:raise ValueError('Wrong oracle frame count')
            counts=row['counts']
            if set(counts)!=set(versions) or any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in counts.values()):
                raise ValueError('Invalid exact per-version atlas counts')
            if not counts['master']==counts['prior']==counts['updated45']:raise ValueError('Legacy versions disagree in oracle ledger')
            if identity[0].startswith('grid_') and any(v!=94*row['frames'] for v in counts.values()):
                raise ValueError('Controlled oracle frame must have exactly 94 atlas keys')
            image=row['oracle_snapshot'];width,height=(800,700) if identity[0]=='font_variations' else (1000,600)
            if image['bytes']!=width*height*4 or len(image['sha256'])!=64 or any(c not in '0123456789abcdef' for c in image['sha256']):
                raise ValueError('Invalid native oracle RGBA record')
            values[identity]=row
        if set(values)!=expected:raise ValueError('Incomplete native oracle phases')
        configurations[key]=values
    if set(configurations)!={(font,dpi) for font in ('stock','vollkorn','ptsans') for dpi in (1,2)}:
        raise ValueError('Native oracle must cover all three fonts at both DPRs')
    return configurations
def verify_record(record,phases,versions):
    path=Path(record['path'])
    if not path.is_file() or path.stat().st_size!=record['bytes'] or sha(path)!=record['sha256']:
        raise ValueError('Native oracle ledger identity changed')
    return load_ledger(path,phases,versions)
def phase_counts(rows,versions):
    frames={int(row['frames']) for row in rows}
    values={version:{int(row['new_atlas_entries']) for row in rows if row['version']==version} for version in versions}
    if len(frames)!=1 or any(len(counts)!=1 for counts in values.values()):
        raise ValueError('Frame or atlas counts vary within a version across trials/blocks')
    counts={version:next(iter(values[version])) for version in versions}
    return next(iter(frames)),next(iter(counts.values())) if len(set(counts.values()))==1 else counts
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',type=Path,default=Path(__file__).resolve().parent/'runtime')
    parser.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent/'bundle')
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'validation-overlay')
    args=parser.parse_args();runtime=args.runtime.resolve(strict=True);bundle=args.bundle.resolve(strict=True);out=args.output.resolve()
    if out.exists():parser.error('--output must be fresh')
    out.mkdir(parents=True)
    originals={}
    for name in ('run.py','summarize.py','sequence_totals.py','build_replay.py','verify_ready.py','experiment.json'):
        source=runtime/'core'/name;shutil.copy2(source,out/name);originals[str(source)]=sha(source)
    for name in ('independent_raw_replay_audit.py','independent_audit_math.py','benchlib.py'):
        source=bundle/'scripts'/name;shutil.copy2(source,out/name);originals[str(source)]=sha(source)
    (out/'oracle_ledger.py').write_text(HELPER)
    run=out/'run.py'
    replace(run,'def validate_block(rows):',
        'def validate_block(rows,font,dpi,ledger):')
    old="""    expected = keys(rows['master'])
    for version in VERSIONS:
        if keys(rows[version]) != expected:
            raise ValueError(f'master/{version} frame or atlas-entry counts differ')
"""
    new="""    if set(rows)!=set(VERSIONS):raise ValueError('Missing/extra block versions')
    legacy=keys(rows['master'])
    for version in ('prior','updated45'):
        if keys(rows[version])!=legacy:raise ValueError(f'master/{version} legacy counts differ')
    phases=ledger[font,int(dpi)]
    for version in VERSIONS:
        for row in rows[version]:
            oracle=phases[row['scene'],row['phase']]
            actual=(int(row['frames']),int(row['new_atlas_entries']))
            expected=(oracle['frames'],oracle['counts'][version])
            if actual!=expected:raise ValueError(f'Exact oracle counts differ: {font}/DPR{dpi}/{version}/{row["scene"]}/{row["phase"]}: {actual} != {expected}')
"""
    replace(run,old,new)
    replace(run,"    parser.add_argument('--root', type=Path, default=ROOT)","    parser.add_argument('--root', type=Path, required=True)")
    replace(run,"    parser.add_argument('--output', type=Path, required=True)","    parser.add_argument('--output', type=Path, required=True)\n    parser.add_argument('--oracle-ledger',type=Path,required=True)")
    replace(run,"    root = args.root.resolve(strict=True)","    from oracle_ledger import verify_record\n    ledger_record=info(args.oracle_ledger)\n    ledger=verify_record(ledger_record,PHASES,VERSIONS)\n    root = args.root.resolve(strict=True)")
    replace(run,"        'control_font_files': controls, 'sources': sources, 'runner_sources': runner,",
        "        'control_font_files': controls, 'sources': sources, 'runner_sources': runner,\n"
        "        'oracle_ledger':ledger_record,\n"
        "        'validation_reference':'Prior/updated45 retain exact master counts/pixels; final matches independently keyed native-master phase-offset oracle counts/pixels; old-master differences retained',")
    replace(run,"    font_info = {name: info(fonts[name]) for name in args.fonts}",
        "    font_info = {name: info(fonts[name]) for name in args.fonts}\n"
        "    ledger_data=json.loads(args.oracle_ledger.read_text())\n"
        "    if ledger_data['master_binary']['sha256']!=binary_info['master']['sha256'] or Path(ledger_data['master_binary']['path']).resolve()!=binaries['master']:raise ValueError('Oracle baseline executable differs from cohort master')\n"
        "    for capture in ledger_data['launches']:\n"
        "        if capture['font'] in args.fonts and int(capture['dpi']) in args.dpis and capture['font_sha256']!=font_info[capture['font']]['sha256']:raise ValueError('Native oracle font differs from cohort font')")
    replace(run,'            validate_block(block_rows)','            validate_block(block_rows,font,dpi,ledger)')
    replace(run,"                    provenance['pixel_comparisons'].extend(comparisons)",
        "                    if version=='final':\n"
        "                        for comparison in comparisons:\n"
        "                            scene,phase=comparison['snapshot'][:-5].split('-',1)\n"
        "                            oracle=ledger[font,int(dpi)][scene,phase]['oracle_snapshot']\n"
        "                            reference=info(oracle['path'])\n"
        "                            if reference['bytes']!=oracle['bytes'] or reference['sha256']!=oracle['sha256']:raise ValueError('Native oracle snapshot identity changed')\n"
        "                            comparison['original_master_rgba_identical']=comparison['rgba_identical']\n"
        "                            comparison['reference_kind']='native-master-phase-offset-oracle'\n"
        "                            comparison['oracle']=reference\n"
        "                            comparison['rgba_identical']=Path(reference['path']).read_bytes()==Path(comparison['candidate']['path']).read_bytes()\n"
        "                    else:\n"
        "                        for comparison in comparisons:comparison['reference_kind']='legacy-master'\n"
        "                    provenance['pixel_comparisons'].extend(comparisons)")
    replace(run,"    provenance['complete']=True", "    if info(args.oracle_ledger)!=ledger_record:raise ValueError('Native oracle ledger changed during measurement')\n    verify_record(ledger_record,PHASES,VERSIONS)\n    provenance['complete']=True")
    summary=out/'summarize.py'
    replace(summary,'from run import PHASES, VERSIONS, parse_rows, validate_block',
        'from run import PHASES, VERSIONS, parse_rows, validate_block\nfrom oracle_ledger import phase_counts, verify_record')
    replace(summary,"    expected_processes=metadata['blocks']", "    ledger=verify_record(metadata['oracle_ledger'],PHASES,VERSIONS)\n    expected_processes=metadata['blocks']")
    replace(summary,'    for values in blocks.values():\n        validate_block(values)',
        '    for (_,font,dpi),values in blocks.items():\n        validate_block(values,font,dpi,ledger)')
    replace(summary,"        writer.writerows(rows)",
        "        writer.writerows({**row,'new_atlas_entries':json.dumps(row['new_atlas_entries'],sort_keys=True)} if isinstance(row.get('new_atlas_entries'),dict) else row for row in rows)")
    old="""            counts={(int(row['frames']),int(row['new_atlas_entries'])) for row in rows}
            if len(counts)!=1:
                raise ValueError(f'workload counts differ across blocks/versions: {font}/{dpi}/{scene}/{phase}')
            frames,atlas=next(iter(counts))"""
    replace(summary,old,'            frames,atlas=phase_counts(rows,VERSIONS)')
    replace(summary,"        'provenance_files':{mode:str(root/f'{mode}-provenance.json') for mode in provenance},",
        "        'provenance_files':{mode:str(root/f'{mode}-provenance.json') for mode in provenance},\n"
        "        'oracle_ledgers':{mode:value['oracle_ledger'] for mode,value in provenance.items()},\n"
        "        'count_validation':'Exact per-version oracle ledger; master/prior/updated45 equal, final matches independent native phase-offset identity; unequal counts recorded as a JSON version map',")
    sequence=out/'sequence_totals.py'
    replace(sequence,'from run import PHASES, VERSIONS','from run import PHASES, VERSIONS\nfrom oracle_ledger import phase_counts')
    old="""            counts={(row['frames'],row['new_atlas_entries']) for row in data}
            if len(counts)!=1:
                raise ValueError(f'frame or atlas counts vary across complete sequences: {font}/{dpi}/{scene}')
            frames,atlas=next(iter(counts))"""
    replace(sequence,old,'            frames,atlas=phase_counts(data,VERSIONS)')
    replace(sequence,"        'provenance_files':provenance,",
        "        'provenance_files':provenance,\n"
        "        'count_validation':'Exact per-version phase oracle ledger revalidated by read_mode; totals stable within each version; unequal atlas totals recorded as a JSON version map',")
    audit=out/'independent_raw_replay_audit.py'
    replace(audit,"    factors=defaultdict(set);seen=set();sources=[path,root/(mode+'-results.csv')]",
        "    oracle_record=metadata['oracle_ledger'];oracle_path=resolve_path(oracle_record['path'])\n"
        "    assert oracle_path.stat().st_size==oracle_record['bytes'] and digest(oracle_path)==oracle_record['sha256']\n"
        "    oracle=json.loads(oracle_path.read_text())\n"
        "    assert oracle['schema']==1 and oracle['complete'] is True and oracle['versions']==versions\n"
        "    assert oracle['oracle_label']=='native-master-offset-oracle'\n"
        "    proofs={}\n"
        "    for proof_kind in ('oracle_prepare','oracle_build'):\n"
        "        record=oracle[proof_kind];proof_path=resolve_path(record['path']);assert digest(proof_path)==record['sha256']\n"
        "        proofs[proof_kind]=json.loads(proof_path.read_text());assert proofs[proof_kind]['complete'] is True\n"
        "    assert proofs['oracle_prepare']['label']=='native-master-offset-oracle' and proofs['oracle_prepare']['changed_files']==['src/text.rs']\n"
        "    assert proofs['oracle_build']['prepare_sha256']==oracle['oracle_prepare']['sha256']\n"
        "    assert oracle['master_binary']['sha256']==metadata['binaries']['master']['sha256']\n"
        "    captures=oracle['launches'];assert len(captures)==12 and all(row['complete'] for row in captures)\n"
        "    assert {(row['font'],int(row['dpi']),row['label']) for row in captures}=={(font,dpi,label) for font in ('stock','vollkorn','ptsans') for dpi in (1,2) for label in ('master','oracle')}\n"
        "    for capture in captures:\n"
        "        if capture['font'] in metadata['fonts'] and int(capture['dpi']) in metadata['dpis']:assert capture['font_sha256']==metadata['font_files'][capture['font']]['sha256']\n"
        "    ledger={}\n"
        "    expected_phases={(scene,phase) for scene,phases in PHASES.items() for phase in phases}\n"
        "    for configuration in oracle['configurations']:\n"
        "        configuration_key=(configuration['font'],int(configuration['dpi']));assert configuration_key not in ledger\n"
        "        phase_rows={}\n"
        "        for row in configuration['phases']:\n"
        "            key=(row['scene'],row['phase']);assert key in expected_phases and key not in phase_rows\n"
        "            assert row['frames']==PHASES[key[0]][key[1]] and set(row['counts'])==set(versions)\n"
        "            assert all(isinstance(value,int) and not isinstance(value,bool) and value>=0 for value in row['counts'].values())\n"
        "            assert row['counts']['master']==row['counts']['prior']==row['counts']['updated45']\n"
        "            if key[0].startswith('grid_'):assert all(value==94*row['frames'] for value in row['counts'].values())\n"
        "            phase_rows[key]=row\n"
        "        assert set(phase_rows)==expected_phases;ledger[configuration_key]=phase_rows\n"
        "    assert set(ledger)=={(font,dpi) for font in ('stock','vollkorn','ptsans') for dpi in (1,2)}\n"
        "    factors=defaultdict(set);seen=set();sources=[path,root/(mode+'-results.csv'),oracle_path]")
    replace(audit,"            factors[launch['font'],launch['dpi'],row['scene'],row['phase']].add((frames,entries))",
        "            expected_work=ledger[launch['font'],int(launch['dpi'])][row['scene'],row['phase']]\n"
        "            assert (frames,entries)==(expected_work['frames'],expected_work['counts'][launch['version']])\n"
        "            factors[launch['font'],launch['dpi'],row['scene'],row['phase'],launch['version']].add((frames,entries))")
    replace(audit,'    return metadata,rows,sources','    return metadata,rows,sources,ledger')
    replace(audit,'    data={};phase_values=defaultdict(dict);sequence_values=defaultdict(dict);fingerprints={};raw_checks=[]',
        '    data={};oracle_counts={};phase_values=defaultdict(dict);sequence_values=defaultdict(dict);fingerprints={};raw_checks=[]')
    replace(audit,'        metadata,rows,sources=validate_raw(root,mode,versions);data[mode]=metadata',
        '        metadata,rows,sources,ledger=validate_raw(root,mode,versions);data[mode]=metadata;oracle_counts[mode]=ledger')
    replace(audit,"            phase=row.get('phase');identity=(*config,phase,row['metric'],row['reference_version'],row['candidate_version'])",
        "            phase=row.get('phase');identity=(*config,phase,row['metric'],row['reference_version'],row['candidate_version'])\n"
        "            ledger=oracle_counts[mode][row['font'],int(row['dpi'])]\n"
        "            if kind=='phase':\n"
        "                expected_counts=ledger[row['scene'],phase]['counts'];assert int(row['frames'])==PHASES[row['scene']][phase]\n"
        "            else:\n"
        "                expected_counts={version:sum(ledger[row['scene'],p]['counts'][version] for p in PHASES[row['scene']]) for version in versions}\n"
        "                assert int(row['reported_frames'])==sum(PHASES[row['scene']].values())\n"
        "            expected_counts=next(iter(expected_counts.values())) if len(set(expected_counts.values()))==1 else expected_counts\n"
        "            reported_counts=json.loads(row['new_atlas_entries']);assert reported_counts==expected_counts")
    # No runtime or original bundle file is patched, including readiness guards.
    for path in out.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
    if any(sha(path)!=checksum for path,checksum in originals.items()):raise ValueError('Original input changed while preparing overlay')
    proof={'schema':1,'complete':True,'runtime':str(runtime),'bundle':str(bundle),'original_file_sha256':originals,
        'prepared_provenance_sha256':sha(runtime/'prepare-provenance.json'),'preparer_sha256':sha(__file__),
        'overlay_files':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},
        'policy':'Read-only driver overlay; original runtime/bundle/builds unchanged; mandatory exact native oracle ledger, no broad count exceptions; original master pixel differences retained'}
    (out/'overlay-provenance.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    print(out)

if __name__=='__main__':main()
