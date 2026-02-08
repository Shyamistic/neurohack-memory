
import os
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    exclude_dirs = {'__pycache__', '.git', 'venv', 'node_modules', 'artifacts', 'docs/brain'}
    exclude_files = {'neurohack_submission.zip', 'neurohack_submission_final.zip', '.env', 'create_submission.py', 'create_submission_final.py', 'debug_eval.py'}
    
    for root, dirs, files in os.walk(path):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files:
                continue
            if file.endswith('.pyc') or file.endswith('.DS_Store'):
                continue
                
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, path)
            ziph.write(file_path, arcname)

if __name__ == '__main__':
    zip_filename = 'neurohack_submission_final.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir('.', zipf)
    print(f"Created {zip_filename}")
