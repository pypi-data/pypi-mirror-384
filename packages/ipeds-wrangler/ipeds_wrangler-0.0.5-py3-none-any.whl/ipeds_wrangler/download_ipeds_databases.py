# Import modules
import os
from pathlib import Path
import platformdirs
import requests
from bs4 import BeautifulSoup
import zipfile
from access_parser import AccessParser

# Define download function
def download_databases(url = "https://nces.ed.gov/ipeds/use-the-data/download-access-database", download_directory = "ipeds_databases"):
    """
    Download IPEDS data from NCES.
    """
    # Identify .zip files
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')

    # Make zip_url_list to contain all .zip URLs
    zip_url_list = []

    # Find all .zip links and append them to the list
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.zip'):
            # Make a full URL if link is relative
            if not href.startswith(('http://', 'https://')):
                full_zip_url = requests.compat.urljoin(url, href)
            else:
                full_zip_url = href
            zip_url_list.append(full_zip_url)
    
    # Select the last 4 in the URLs list (4 most recent years)
    zip_url_list = zip_url_list[-4:]

    # Download .zip files
    try:
        # Get Desktop path and create Path object
        desktop_path = platformdirs.user_desktop_dir()
        download_directory_path = Path(desktop_path) / download_directory

        # Create the download directory if it does not already exist
        os.makedirs(download_directory_path, exist_ok=True)
        print(f"Downloading IPEDS databases to {download_directory_path}")

    except Exception as e:
        print(f"Error creating download directory: {e}")

    for zip_url in zip_url_list:
        try:
            # Define filepath for each .zip file
            zip_filename = os.path.basename(zip_url)
            filepath = os.path.join(download_directory_path, zip_filename)

            # Skip downloading existing .zip files
            if os.path.exists(filepath):
                print(f"{filepath} already exists. Skipping download.")
            else:
                zip_response = requests.get(zip_url, stream=True)
                zip_response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in zip_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Successfully downloaded {zip_url}")

        # Display any errors
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {zip_url}: {e}")
        except Exception as e:
            print(f"Error downloading {zip_url}: {e}")

    # Extract .accdb files from .zip files
    print(f"Extracting IPEDS databases...")

    for filename in sorted(os.listdir(download_directory_path)):
        if filename.endswith(".zip"):
            zip_filepath = os.path.join(download_directory_path, filename)
            try:
                with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        # Ignoring directories, extract only .accdb files
                        if not member.endswith('/') and member.endswith('.accdb'):
                            # do not create subdirectories
                            base_filename = os.path.basename(member)
                            # Handle potential root directories (empty string)
                            if base_filename:
                                source = zip_ref.open(member)
                                target_path = os.path.join(download_directory_path, base_filename)
                                
                                with open(target_path, "wb") as target:
                                    target.write(source.read())
                                print(f"Successfully extracted '{member}'")

            # Display any errors
            except zipfile.BadZipFile:
                print(f"Error extracting {filename}: Not a valid .zip file.")
            except Exception as e:
                print(f"Error extracting {filename}: {e}")

    # Parse .accdb files
    for filename in sorted(os.listdir(download_directory_path)):
            if filename.endswith('.accdb'):
                db_filepath = os.path.join(download_directory_path, filename)
                try:
                    db = AccessParser(db_filepath)
                    print(db_filepath)
                    # # count tables in catalog
                    # print(db_filepath)
                    # print(len(db.catalog.keys()))
                    # # display table catalog
                    # print("Tables in the database:")
                    for table_name in db.catalog.keys():
                        if table_name.startswith('HD'):
                            print(table_name)
    
                # Display any errors
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")

# Call function
download_databases()