%pip install faker

# next cell
import sys
sys.path.append("/Workspace/m*********@outlook.com/motor-insurance-lakehouse/generator")   # adjust the path
import generate_data

BASE = "/Volumes/dev_insurance/landing/raw"
summary = generate_data.main(BASE)
