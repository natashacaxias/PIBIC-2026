#!/usr/bin/env python3
"""Download, inspeção e geração das condições de fumaça do QueensCAMP.

  python scripts/dataset.py download --dest /data/queenscamp_raw --sequences 09 --kind full
  python scripts/dataset.py inspect /data/queenscamp/09
  python scripts/dataset.py smoke --sequences 09

IDs do Google Drive copiados de https://larocs.github.io/queenscamp-dataset (out/2026).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / 'smoke_emulation'))
from lib.queenscamp import load_config, sequence_dir  # noqa: E402

# seq -> (Full Sequence, Bag)
DRIVE_IDS = {
    '01': ('1nqa7ft5MKF0wcJd9GyHwLBtAL7D1OV47', '1xjIQjClK1niVoXDSxSNxQe76FkAcNAff'),
    '02': ('1D1wiifPuNYeotUNdMXFZDKXJJ_X_aiuF', '15fQOuLZwFsG5um1BvkKsW7BzuF-Uz_bn'),
    '03': ('16zeLzSl9FB-43kvDg77Xiva5teQYdw3r', '1fmWsYXq9EW7YzyX1CuKLe_LLKXuKcL1p'),
    '04': ('1baHAq8XdyKSh1rX_6fpZ7zJKM29UW1wZ', '1jhRtQ_JpK9KXfJeLONSr0MGfzx0a1VLy'),
    '05': ('1WmULSIyx9UtDKhr1H_0DOEazRkbOMIm3', '1PexbcMAuAYAPID1NDunT5uqExfiDSxhF'),
    '06': ('1h_c-l19GEGLTc-gLBfEbZCbZOK-KFRDt', '1YSHISkkQpSvU5GGhAY6ZsPaD8WIbrv0x'),
    '07': ('1GJM3pz_BnLuGTq4CytuYEAZqraqH_ck3', '1qXwq9cl_mcNPt2ANd8gg6Eqn6QjHwf9V'),
    '08': ('1jKQo7DGmUXfP35yZ70NiBR6hqwSSa84e', '1qF4QE2gLNhoUIO-KlBznHpQIck-p9g97'),
    '09': ('1ja_qvTYSmGJPxoVAm89Ay2pIiDLXjvw4', '1RgAflLe3xeAsIP-RgxrkaKOP7L_zEANw'),
    '10': ('1RBpzd42HbjEOmdjLONgsXi3GgDy_AyUF', '1TSWsITjPNu-nBko9QufAy7LLEdaOTTtu'),
    '11': ('1XmyRndO7CKdTVmeuZfYUzd5okKbgVeZM', '1tOKUJKg8pC2e2RcZs5JQ_95SDt62Ps5j'),
    '12': ('13966F62XT715PDz5STvwla8EAftOyzKJ', '1reJzXP6iS9ij_LSm4sJ6MqVEtvRJHCdB'),
    '13': ('1MVWvxYA8ZWXM5yB0ZtEqjHl3AGdPwrKz', '13K2wL0HaefcJ6UMjC3W5YIOQGENhAEca'),
    '14': ('1EuQpPZC4vqVSyoHel3GADSzbrdPbZswv', '1lfcyFHUTmP4saGPSl5LaOgMF3zOYAocl'),
    '15': ('1FsjWzlUupiUxAfD6hBum70dqTznlTzQQ', '1K-0tqTxQlgvEluhMf_exRRYFQkKH5i8u'),
    '16': ('1MCcSApcisMupuyX0K09A8kjQl7aIG7M4', '1kUfufHLgd9Q9Z3Eb1gAdgDXD3rPxdA6P'),
}
CAMERA_INFO_IDS = {'camera_info_rgb': '16JEOw3xNZu8f79BG29LN6BoParwQUhqU',
                   'camera_info_depth': '1IqAv9xRtl1qZ4iXHHOcg_rNLyAPKUIw1'}


def sha256(path, chunk=1 << 22):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(chunk), b''):
            digest.update(block)
    return digest.hexdigest()


def download(dest, sequences, kind):
    import gdown
    dest.mkdir(parents=True, exist_ok=True)
    log_file = dest / 'downloads.json'
    log = json.loads(log_file.read_text()) if log_file.exists() else []
    targets = [(name, file_id) for name, file_id in CAMERA_INFO_IDS.items()]
    targets += [(f'{seq}_{kind}', DRIVE_IDS[seq][0 if kind == 'full' else 1]) for seq in sequences]
    for name, file_id in targets:
        path = gdown.download(id=file_id, output=str(dest) + '/', resume=True, quiet=False)
        if not path:
            print(f'falha ao baixar {name} ({file_id})', file=sys.stderr)
            continue
        path = Path(path)
        log.append({'name': name, 'drive_id': file_id, 'file': path.name, 'bytes': path.stat().st_size,
                    'sha256': sha256(path), 'downloaded_at': datetime.now(timezone.utc).isoformat()})
        log_file.write_text(json.dumps(log, indent=2), encoding='utf-8')
        print(f'ok {name}: {path} ({path.stat().st_size / 2**30:.2f} GiB)')


def inspect(seq_dir):
    """Resumo do layout de uma sequência extraída, para preencher config/experiment.json."""
    import cv2
    import numpy as np
    seq_dir = Path(seq_dir)
    report = {'seq_dir': str(seq_dir), 'directories': {}, 'text_files': {}}
    for d in sorted(p for p in seq_dir.rglob('*') if p.is_dir()):
        pngs = sorted(d.glob('*.png'))
        if not pngs:
            continue
        sample = cv2.imread(str(pngs[0]), cv2.IMREAD_UNCHANGED)
        info = {'n_png': len(pngs), 'first': pngs[0].name, 'shape': list(sample.shape), 'dtype': str(sample.dtype)}
        if sample.dtype == np.uint16:
            valid = sample[sample > 0]
            info['zero_fraction'] = float((sample == 0).mean())
            info['median_nonzero_raw'] = float(np.median(valid)) if valid.size else None
            if valid.size:
                info['median_m_if_mm'] = info['median_nonzero_raw'] / 1000.0
                info['median_m_if_5000'] = info['median_nonzero_raw'] / 5000.0
        report['directories'][str(d.relative_to(seq_dir))] = info
    for txt in sorted(seq_dir.rglob('*.txt')):
        with open(txt, encoding='utf-8', errors='replace') as f:
            report['text_files'][str(txt.relative_to(seq_dir))] = [next(f, '').rstrip() for _ in range(3)]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print('\nUse: pastas uint16 → depth_dir; pastas RGB de cada falha → conditions.*.rgb_dir; '
          'a escala cuja mediana fica entre 1 e 5 m (sala de 5 × 7,5 m) → depth_scale.', file=sys.stderr)
    return report


def smoke(cfg, sequences):
    from emulate_sequence import emulate_sequence
    data, smoke_cfg = cfg['dataset'], cfg['smoke']
    rgb_dir = cfg['conditions']['original']['rgb_dir']
    for seq in sequences or cfg['sequences']:
        for name, cond in cfg['conditions'].items():
            if cond['kind'] != 'smoke':
                continue
            out = Path(cfg['paths']['smoke_root']) / seq / name
            if (out / 'smoke_meta.json').exists():
                print(f'já existe: {out}')
                continue
            meta = emulate_sequence(sequence_dir(cfg, seq) / rgb_dir, sequence_dir(cfg, seq) / data['depth_dir'], out,
                                    cond['visibility_m'], data['depth_scale'], tuple(smoke_cfg['atmospheric_light']),
                                    smoke_cfg['max_depth_m'])
            print(f"seq {seq} {name}: {meta['n_frames']} frames, t̄={meta['mean_transmission']['mean']:.3f}")


def dehaze(cfg, sequences, conditions):
    """Aplica o Dark Channel Prior às condições de origem (baseline NATASHA-17)."""
    from lib.queenscamp import condition_rgb_dir
    from dcp import dehaze_sequence
    params = dict(cfg['dehaze'])
    mode = params.pop('airlight_mode')
    targets = conditions or [c for c, spec in cfg['conditions'].items() if spec['kind'] == 'dehaze']
    for seq in sequences or cfg['sequences']:
        for name in targets:
            cond = cfg['conditions'][name]
            if cond['kind'] != 'dehaze':
                raise ValueError(f'{name} não é uma condição de dehazing')
            out = Path(cfg['paths']['dehaze_root']) / seq / name
            if (out / 'dcp_meta.json').exists():
                print(f'já existe: {out}')
                continue
            meta = dehaze_sequence(condition_rgb_dir(cfg, seq, cond['source']), out, mode, **params)
            print(f"seq {seq} {name}: {meta['n_frames']} quadros, A={meta['airlight_rgb_median']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    dl = sub.add_parser('download')
    dl.add_argument('--dest', type=Path, required=True)
    dl.add_argument('--sequences', nargs='+', default=sorted(DRIVE_IDS))
    dl.add_argument('--kind', choices=['full', 'bag'], default='full')
    ins = sub.add_parser('inspect')
    ins.add_argument('seq_dir')
    sm = sub.add_parser('smoke')
    sm.add_argument('--config', default=str(ROOT / 'config/experiment.json'))
    sm.add_argument('--sequences', nargs='+')
    dh = sub.add_parser('dehaze', help='DCP sobre as condições de origem (rodar depois de smoke)')
    dh.add_argument('--config', default=str(ROOT / 'config/experiment.json'))
    dh.add_argument('--sequences', nargs='+')
    dh.add_argument('--conditions', nargs='+')
    args = parser.parse_args()
    if args.command == 'download':
        download(args.dest, args.sequences, args.kind)
    elif args.command == 'inspect':
        inspect(args.seq_dir)
    elif args.command == 'smoke':
        smoke(load_config(args.config), args.sequences)
    else:
        dehaze(load_config(args.config), args.sequences, args.conditions)
    return 0


if __name__ == '__main__':
    sys.exit(main())
