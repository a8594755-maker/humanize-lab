"""Download only pinned inference assets; no training and no API key required."""
from pathlib import Path
import json
from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parent
MODELS = {
    'guide': ('fakespot-ai/roberta-base-ai-text-detection-v1', 'f9cdb14d1f8b105f597d80fa7b56f20c6ea0e9db'),
    'holdout': ('desklib/ai-text-detector-v1.01', '5fdea974cd4287c61674951ec78803aa274e2fb7'),
    'similarity': ('sentence-transformers/all-MiniLM-L6-v2', '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'),
    'nli': ('cross-encoder/nli-deberta-v3-small', 'fa2804872c3b4bd748f38c0185cc85775361e735'),
}

def main():
    manifest_path = ROOT / 'models' / 'manifest.json'
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    for name, (repo, revision) in MODELS.items():
        revision = manifest.get(name, {}).get('revision') or revision or HfApi().model_info(repo).sha
        print(f'Downloading {name}: {repo}@{revision}', flush=True)
        snapshot_download(repo, revision=revision, local_dir=ROOT / 'models' / name,
                          allow_patterns=['*.json', '*.txt', '*.model', 'model.safetensors', 'README.md', 'LICENSE*'],
                          ignore_patterns=['onnx/*', 'openvino/*', '*/train*'], max_workers=3)
        manifest[name] = {'repo': repo, 'revision': revision}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('All four local models downloaded.', flush=True)

if __name__ == '__main__':
    main()
