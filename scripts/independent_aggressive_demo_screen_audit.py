#!/usr/bin/env python3
"""Independently verify exploratory demo effects with exact rational arithmetic.

Read each original process stdout rather than the derived effects CSV. This
auditor supports either broad or supplement exploration without changing its
arithmetic. It never executes a benchmark, changes a frozen input, or estimates
confidence intervals from the two exploratory blocks.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

PATH_MAP = []
ALLOW_MISSING_BINARIES = False

def resolve(path):
    value = str(path)
    for old,new in PATH_MAP:
        if value==old or value.startswith(old.rstrip('/')+'/'):
            return Path(new+value[len(old):])
    return Path(value)

PHASES = {'first_paint':1,'warm':30,'zoom_in':12,'zoom_out':12,'pan':10}
ENDPOINTS = ('draw_us','submit_us','complete_us')


def require(value, message):
    if not value:
        raise ValueError(message)


def info(path):
    reported=str(Path(path));actual=resolve(path).resolve(strict=True);raw=actual.read_bytes()
    return {'path':reported,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def load(path):
    return json.loads(resolve(path).read_text())


def median(values):
    values=sorted(values);n=len(values)
    return values[n//2] if n%2 else (values[n//2-1]+values[n//2])/2


def close(actual, expected, label):
    difference=abs(Fraction(str(actual))-expected)
    require(difference<=Fraction(1,1000000000), f'{label}: {actual} != {float(expected)}')
    return float(difference)


def archived_guard(root):
    protocol_path = root/'demo-selection-v1/protocol.json'
    protocol=load(protocol_path)
    require(protocol['complete'] and protocol['source_only_protocol'],'Frozen protocol incomplete')
    require(info(protocol['selection']['path'])==protocol['selection'],'Frozen selection changed')
    require(info(protocol['driver']['path'])==protocol['driver'],'Frozen wrapper source changed')
    selection=load(protocol['selection']['path'])
    for name in ('collector','native_protocol','native_ranking','static_inspection','freezer'):
        require(info(selection[name]['path'])==selection[name],'Frozen input changed: '+name)
    for name in ('static_priors','demo_corpus_proof','source_derivation'):
        if name in selection:
            require(info(selection[name]['path'])==selection[name],'Frozen input changed: '+name)
    if 'native_rejection' in selection:
        for name in ('stdout_info','stderr_info'):
            record=selection['native_rejection'][name]
            require(info(record['path'])==record,'Retained native rejection changed')
    for font in selection['fonts']:
        require(info(font['path'])=={k:font[k] for k in ('path','bytes','sha256')},'Font changed: '+font['label'])
    identity=selection['input_identity']
    parent=Path(identity['demo_prepare']['path']).parent.parent
    analyzer_path=parent/'demo-confirmation-analysis-v1/analyze_demo_confirm.py'
    source_proof_path=parent/'demo-confirmation-analysis-v1/source-preparation.json'
    source_proof=load(source_proof_path)
    require(source_proof['complete'] and source_proof['source_only'],'Identity adapter preparation incomplete')
    require(info(source_proof['preparer']['path'])==source_proof['preparer'],'Identity adapter generator changed')
    bound=[entry for entry in source_proof['changes'] if entry['after']['path']==str(analyzer_path)]
    require(len(bound)==1 and info(analyzer_path)==bound[0]['after'],'Identity adapter source changed')
    spec=importlib.util.spec_from_file_location('frozen_demo_identity_adapter',resolve(analyzer_path))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    binary_records=[*identity['binaries'].values(),identity['oracle_binary']]
    class ArchiveReader(module.Reader):
        def __init__(self):
            super().__init__(dict(PATH_MAP),False)
            self.missing_compiled_bodies=[]
        def check_info(self,record,live=False):
            if live:
                require(record in binary_records,'Missing-body policy can only apply to recorded executables')
                if not self.resolve(record['path']).exists():
                    require(ALLOW_MISSING_BINARIES,'Executable is missing; pass explicit --allow-missing-binaries for an archive audit')
                    self.missing_compiled_bodies.append(record)
                    return
            super().check_info(record,live=False)
    reader=ArchiveReader()
    module.audit_identity(reader,identity)
    # The wrapper/collector are checked as source bytes and never imported or
    # called. Stored source identity is verified by the frozen adapter instead.
    require(selection['collector']==identity['active_collector'],'Selected collector differs from source identity')
    return protocol,selection,{
        'allow_missing_binaries_explicit':ALLOW_MISSING_BINARIES,
        'omitted_compiled_bodies':reader.missing_compiled_bodies,
        'identity_adapter':info(analyzer_path),'identity_adapter_source_proof':info(source_proof_path),
        'font_source_build_dependency_metadata_checks_retained':True,
        'wrapper_and_collector_imported':False,
        'path_map':dict(PATH_MAP)}

def audit(root, output):
    root=resolve(root)
    wrapper=root/'run_aggressive_demo_screen.py'
    protocol,selection,archive_policy=archived_guard(root)
    campaign=root/'demo-screen-v1'
    analysis_path=campaign/'independent-analysis/analysis.json'
    analysis=load(analysis_path)
    require(analysis['complete'] and analysis['no_confidence_intervals'], 'Analysis incomplete or unexpected CI scope')
    provenance=load(campaign/'cpu-provenance.json')
    require(provenance['complete'] and provenance['versions']==['master','final'] and provenance['dpis']==[2] and provenance['blocks']==2 and provenance['trials_per_process']==3, 'Unexpected campaign dimensions')
    require(provenance['selection_manifest']==protocol['selection'] and provenance['identity']==selection['input_identity'], 'Frozen inputs differ')
    labels=[f['label'] for f in selection['fonts']]
    expected={(font,block,version) for font in labels for block in (1,2) for version in ('master','final')}
    process={};original_rows=0;atlas=[]
    combined=[]
    for launch in provenance['launches']:
        key=launch['font'],launch['block'],launch['version']
        require(key in expected and key not in process and launch['validated'] and launch['exit_code']==0,'Missing/duplicate/failed process')
        require(info(launch['stdout'])==launch['stdout_info'] and info(launch['stderr'])==launch['stderr_info'],'Original raw process changed')
        with resolve(launch['stdout']).open(newline='') as stream: rows=list(csv.DictReader(stream))
        original_rows+=len(rows);numeric={}
        for row in rows:
            trial=int(row['trial']);phase=row['phase']
            require(row['scene']=='demo' and 0<=trial<3 and phase in PHASES and int(row['frames'])==PHASES[phase],'Unexpected original raw phase')
            require((trial,phase) not in numeric,'Duplicate raw phase')
            values={endpoint:Fraction(row[endpoint]) for endpoint in ENDPOINTS}
            require(all(value>=0 for value in values.values()),'Negative raw time')
            numeric[trial,phase]=values
            atlas.append({'font':key[0],'block':key[1],'version':key[2],'trial':trial,'phase':phase,'entries':int(row['new_atlas_entries'])})
            combined.append({'backend':'cpu','font':key[0],'dpi':'2','block':str(key[1]),'version':key[2],**row})
        require(set(numeric)=={(trial,phase) for trial in range(3) for phase in PHASES},'Incomplete original process')
        process[key]=numeric
    require(set(process)==expected and original_rows==protocol['expected_raw_rows'],'Incomplete campaign matrix')
    with (campaign/'cpu-results.csv').open(newline='') as stream:
        require(list(csv.DictReader(stream))==combined,'Combined CSV differs from original stdout')
    require(atlas==analysis['original_atlas_counts'],'Original atlas annotations differ')
    expected_order=[]
    for block in range(2):
        for font in labels[block:]+labels[:block]:
            versions=('master','final') if (block+labels.index(font))%2==0 else ('final','master')
            expected_order.extend((font,block+1,version) for version in versions)
    require([(launch['font'],launch['block'],launch['version']) for launch in provenance['launches']]==expected_order,'AB/BA configuration order differs')
    reference={}
    for font in labels:
        for phase in [*PHASES,'sequence_65_frames']:
            for endpoint in ENDPOINTS:
                blocks=[]
                for block in (1,2):
                    record={'block':block}
                    for version in ('master','final'):
                        raw=process[font,block,version]
                        trials=[sum(raw[trial,p][endpoint]*frames for p,frames in PHASES.items()) if phase=='sequence_65_frames' else raw[trial,phase][endpoint] for trial in range(3)]
                        record[version]=median(trials)
                    record['saving']=record['master']-record['final'];blocks.append(record)
                savings=[b['saving'] for b in blocks]
                reference[font,phase,endpoint]={
                    'master_mean_process_median':sum(b['master'] for b in blocks)/2,
                    'final_mean_process_median':sum(b['final'] for b in blocks)/2,
                    'master_minus_final_mean':sum(savings)/2,
                    'paired_block_range':[min(savings),max(savings)],'blocks':blocks,
                    'positive_blocks':sum(v>0 for v in savings),'negative_blocks':sum(v<0 for v in savings)}
    maximum_difference=0.0;seen=set()
    for row in analysis['effects']:
        key=row['font'],row['phase'],row['endpoint']
        require(key in reference and key not in seen,'Unexpected/duplicate derived effect');seen.add(key)
        ref=reference[key]
        for name in ('master_mean_process_median','final_mean_process_median','master_minus_final_mean'):
            maximum_difference=max(maximum_difference,close(row[name],ref[name],str(key)+'/'+name))
        for actual,expected_range in zip(row['paired_block_range'],ref['paired_block_range']):
            maximum_difference=max(maximum_difference,close(actual,expected_range,str(key)+'/range'))
        require(row['positive_blocks']==ref['positive_blocks'] and row['negative_blocks']==ref['negative_blocks'],'Block sign annotation differs')
        require(len(row['blocks'])==2,'Missing derived paired block')
        for actual,wanted in zip(row['blocks'],ref['blocks']):
            require(actual['block']==wanted['block'],'Block identity differs')
            for name in ('master','final','saving'):
                maximum_difference=max(maximum_difference,close(actual[name],wanted[name],str(key)+'/block/'+name))
    require(seen==set(reference),'Missing derived effect')
    require(not output.exists(),'Retain previous audit output')
    result={'complete':True,'auditor':info(Path(__file__)),'wrapper':info(wrapper),
        'protocol':info(root/'demo-selection-v1/protocol.json'),'selection':info(root/'demo-selection-v1/selection.json'),
        'provenance':info(campaign/'cpu-provenance.json'),'analysis':info(analysis_path),
        'processes_checked':len(process),'raw_original_stdout_rows_checked':original_rows,
        'original_atlas_annotations_checked':len(atlas),'phase_sequence_endpoint_effects_checked':len(reference),
        'maximum_absolute_decimal_to_fraction_difference':maximum_difference,
        'method':'Independent exact Fraction parsing and sorted median arithmetic from every original process stdout. Verify phase medians, within-trial 65-frame sequences, both paired blocks, means, ranges, signs, raw CSV agreement and AB/BA order. Source/build/font guard reused read-only; no benchmark, CI, exclusion or input mutation.',
        'new_application_pixel_proof':False,'archive_policy':archive_policy}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--path-map',type=Path,help='JSON mapping frozen original roots to extracted archive roots')
    parser.add_argument('--allow-missing-binaries',action='store_true',help='Explicitly allow omitted compiled bodies only; verify every existing body and all fonts/source/build/raw/order identities')
    args=parser.parse_args()
    PATH_MAP=sorted((json.loads(args.path_map.read_text()) if args.path_map else {}).items(),key=lambda pair:-len(pair[0]))
    ALLOW_MISSING_BINARIES=args.allow_missing_binaries
    audit(args.root,args.output)
