#!/usr/bin/env python3
import argparse
import base64
import os
import sys
import tempfile
import subprocess
import shlex

class FFPM:
    def __init__(self):
        self.parser = self._setup_parser()
    
    def _setup_parser(self):
        parser = argparse.ArgumentParser(description='FFPM - File Fusion Package Manager')
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Pack command
        pack_parser = subparsers.add_parser('pack', aliases=['-p'], help='Pack multiple files into one')
        pack_parser.add_argument('files', nargs='+', help='Files to pack')
        pack_parser.add_argument('-o', '--output', help='Output file name', default='packed.ffpm')
        pack_parser.add_argument('-m', '--main', help='Main Python file to run (default: first .py file)')
        
        # Decode command
        decode_parser = subparsers.add_parser('decode', aliases=['-d'], help='Decode packed file')
        decode_parser.add_argument('file', help='Packed file to decode')
        
        # Start command
        start_parser = subparsers.add_parser('start', help='Run packed file')
        start_parser.add_argument('file', help='Packed file to run')
        start_parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments to pass to the script')
        
        return parser
    
    def pack_files(self, files, output_file, main_file=None):
        """Pack multiple files into a single .ffpm file"""
        if not all(os.path.exists(f) for f in files):
            print("Error: One or more files not found")
            return False
        
        # Determine main file
        if main_file and main_file not in files:
            print(f"Error: Main file '{main_file}' not in file list")
            return False
        
        if not main_file:
            # Find first Python file as main
            for f in files:
                if f.endswith('.py'):
                    main_file = f
                    break
        
        with open(output_file, 'w', encoding='utf-8') as out_f:
            out_f.write("#!/usr/bin/env python3\n")
            out_f.write("# FFPM Packed File\n")
            out_f.write("import base64\n")
            out_f.write("import tempfile\n")
            out_f.write("import os\n")
            out_f.write("import sys\n")
            out_f.write("import subprocess\n\n")
            
            out_f.write("def extract_and_run():\n")
            out_f.write("    files_content = {}\n")
            
            # Encode each file (binary for non-text files)
            for file_path in files:
                file_name = os.path.basename(file_path)
                
                # Try to detect if file is text or binary
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # If we can read as text, encode as text
                    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                    out_f.write(f'    files_content["{file_name}"] = {{"content": """{encoded_content}""", "type": "text"}}\n')
                except (UnicodeDecodeError, UnicodeError):
                    # If text reading fails, treat as binary
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    encoded_content = base64.b64encode(content).decode('utf-8')
                    out_f.write(f'    files_content["{file_name}"] = {{"content": """{encoded_content}""", "type": "binary"}}\n')
                
                print(f"Packed: {file_name}")
            
            out_f.write("""
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write all files
        for filename, file_info in files_content.items():
            filepath = os.path.join(temp_dir, filename)
            if file_info["type"] == "text":
                content = base64.b64decode(file_info["content"]).decode('utf-8')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:  # binary
                content = base64.b64decode(file_info["content"])
                with open(filepath, 'wb') as f:
                    f.write(content)
        
        # Run Python main file if exists
        python_files = [f for f in files_content.keys() if f.endswith('.py')]
        if python_files:
            # Add temp directory to Python path
            sys.path.insert(0, temp_dir)
            
            # Determine main file
""")
            
            # Add main file selection logic
            if main_file:
                main_filename = os.path.basename(main_file)
                out_f.write(f'            main_file = "{main_filename}"\n')
            else:
                out_f.write('            main_file = python_files[0] if python_files else None\n')
            
            out_f.write("""
            if main_file and main_file in files_content:
                # Import and run main module
                main_module = main_file.replace('.py', '')
                try:
                    module = __import__(main_module)
                    if hasattr(module, 'main'):
                        module.main()
                    else:
                        print(f"Warning: No main() function found in {main_file}")
                        print("Available files in package:", list(files_content.keys()))
                except Exception as e:
                    print(f"Error running {main_file}: {e}")
                    sys.exit(1)
            else:
                print("No Python main file to execute.")
                print("Extracted files:", list(files_content.keys()))
                print(f"Files are available in: {temp_dir}")
        else:
            print("No Python files in package.")
            print("Extracted files:", list(files_content.keys()))
            print(f"Files are available in: {temp_dir}")

if __name__ == '__main__':
    extract_and_run()
""")
        
        # Make executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(output_file, 0o755)
        
        print(f"Successfully packed {len(files)} files into {output_file}")
        return True
    
    def decode_file(self, packed_file):
        """Decode a packed .ffpm file and extract original files"""
        if not os.path.exists(packed_file):
            print(f"Error: File {packed_file} not found")
            return False
        
        output_dir = packed_file.replace('.ffpm', '_decoded')
        os.makedirs(output_dir, exist_ok=True)
        
        with open(packed_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract base64 encoded content with type information
        import re
        pattern = r'files_content\["([^"]+)"\] = \{"content": """([^"]+)""", "type": "([^"]+)"\}'
        matches = re.findall(pattern, content)
        
        if not matches:
            print("Error: No encoded files found in the packed file")
            return False
        
        for filename, encoded_content, file_type in matches:
            try:
                output_path = os.path.join(output_dir, filename)
                
                if file_type == "text":
                    decoded_content = base64.b64decode(encoded_content).decode('utf-8')
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(decoded_content)
                else:  # binary
                    decoded_content = base64.b64decode(encoded_content)
                    with open(output_path, 'wb') as f:
                        f.write(decoded_content)
                
                print(f"Extracted: {filename} ({file_type})")
            except Exception as e:
                print(f"Error decoding {filename}: {e}")
        
        print(f"All files extracted to: {output_dir}")
        return True
    
    def start_file(self, packed_file, extra_args):
        """Run a packed .ffpm file"""
        if not os.path.exists(packed_file):
            print(f"Error: File {packed_file} not found")
            return False
        
        # Execute the packed file
        try:
            cmd = [sys.executable, packed_file] + extra_args
            result = subprocess.run(cmd)
            return result.returncode == 0
        except Exception as e:
            print(f"Error running {packed_file}: {e}")
            return False
    
    def run(self):
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return
        
        if args.command in ['pack', '-p']:
            self.pack_files(args.files, args.output, args.main)
        elif args.command in ['decode', '-d']:
            self.decode_file(args.file)
        elif args.command == 'start':
            self.start_file(args.file, args.args)

def main():
    ffpm = FFPM()
    ffpm.run()

if __name__ == '__main__':
    main()