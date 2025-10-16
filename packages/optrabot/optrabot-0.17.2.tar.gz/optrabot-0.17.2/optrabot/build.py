import subprocess
import sys

def build_with_frontend():
	"""
	Build the OptraBot but including the build of the frontend.
	"""
	try:
		# Schritt 1: Frontend-Build ausführen
		print("Running frontend build...")
		subprocess.run(["npm", "run", "build"], check=True, cwd="./frontend")
		
		# Schritt 2: Poetry-Build ausführen
		print("Running Poetry build...")
		subprocess.run(["poetry", "build"], check=True)

		print("Build completed successfully!")
	except subprocess.CalledProcessError as e:
		print(f"Error during build: {e}")
		return