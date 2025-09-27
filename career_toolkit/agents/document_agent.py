import subprocess
import json
import os
import tempfile
from typing import Union, Dict, Any
from .data_agent import Resume

class DocumentAgent:
    def compile_typst_document(self, data: Union[Resume, Dict[str, Any]], template_content: str, output_filename: str) -> str:
        """
        Compiles a Typst template with the given data to generate a PDF.

        This method creates a temporary directory to safely handle file operations.
        It writes the user's data to a JSON file and the uploaded template to a .typ file.
        It then calls the Typst CLI to compile the document and returns the path to the output PDF.

        Args:
            data: The user's data (e.g., a Resume Pydantic object or a dict for the cover letter).
            template_content: The string content of the user-uploaded .typ template.
            output_filename: The desired name for the final PDF file (e.g., 'resume.pdf').

        Returns:
            The absolute path to the generated PDF file, or an empty string if compilation fails.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define file paths within the temporary directory
            data_path = os.path.join(temp_dir, 'data.json')
            template_path = os.path.join(temp_dir, 'template.typ')
            output_path = os.path.join(temp_dir, output_filename)

            # 1. Write the data to data.json
            try:
                with open(data_path, 'w') as f:
                    if isinstance(data, Resume):
                        # Use Pydantic's serialization for the Resume model
                        json.dump(data.model_dump(exclude_none=True), f, indent=2)
                    else:
                        # Assume it's a dictionary (for the cover letter)
                        json.dump(data, f, indent=2)
            except (IOError, TypeError) as e:
                print(f"Error writing data to JSON file: {e}")
                return ""

            # 2. Write the template content to template.typ
            try:
                with open(template_path, 'w') as f:
                    f.write(template_content)
            except IOError as e:
                print(f"Error writing template file: {e}")
                return ""

            # 3. Compile the Typst document using the CLI
            # The Typst template should be written to load 'data.json'.
            # Example Typst code: #let data = json("data.json")
            command = [
                'typst',
                'compile',
                template_path,
                output_path
            ]
            
            try:
                # The command is run from within the temp_dir so Typst can find data.json
                result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_dir)
                print("Typst compilation successful.")
                print(result.stdout)
                
                # The PDF is generated in temp_dir, but we need to move it or read it
                # before the directory is cleaned up. Returning the path is not enough.
                # Instead, we'll read the bytes and return them for download.
                with open(output_path, 'rb') as f:
                    pdf_bytes = f.read()
                return pdf_bytes

            except FileNotFoundError:
                print("Error: 'typst' command not found. Please ensure Typst is installed and in your system's PATH.")
                return None # Indicate a specific error
            except subprocess.CalledProcessError as e:
                print("Error during Typst compilation:")
                print(e.stderr)
                return None # Indicate a compilation error

        return None # Should not be reached if successful
