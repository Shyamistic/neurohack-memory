
import os
import zipfile

def zip_directory(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            # Exclude venv and __pycache__
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                # Exclude secrets and junk
                if file == '.env' or file.startswith("debug_") or file == "inspect_db.py":
                    continue
                if file.endswith('.zip') or file.endswith('.sqlite') or file == '.DS_Store' or file.endswith('.ipynb'):
                    continue
                
                # Full path
                file_path = os.path.join(root, file)
                
                # Relative path in zip
                arcname = os.path.relpath(file_path, folder_path)
                
                # Add to zip
                print(f"Adding: {arcname}")
                zipf.write(file_path, arcname)
    
    # Verify critical files are in the zip
    missing = []
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        namelist = zipf.namelist()
        critical = [
            "scripts/ablation_study.py", 
            "scripts/generate_adversarial.py",
            "scripts/evaluate_adversarial.py",
            "demo.py",
            "PPT_OUTLINE.md",
            "README.md",
            "metrics_proof.md",
            "config.yaml",
            ".env.example",
            "artifacts/metrics.json",
            "run_demo.sh",
            "run_demo.bat",
            "SYSTEM_REPORT.md",
            "GAMMA_PROMPT.md"
        ]
        for f in critical:
            if f not in namelist:
                 missing.append(f)
    
    if missing:
        with zipfile.ZipFile(zip_path, 'a') as zipf:
            for f in missing:
                 if os.path.exists(f):
                     print(f"Force adding critical file: {f}")
                     zipf.write(f, f)
                 else:
                     print(f"WARNING: Critical file missing: {f}")

if __name__ == "__main__":
    out_file = "neurohack_submission.zip"
    zip_directory(".", out_file)
    print(f"\n✓ Created submission zip: {out_file}")
