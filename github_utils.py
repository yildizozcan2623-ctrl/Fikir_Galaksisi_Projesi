import requests
import base64
from urllib.parse import urlparse

def extract_github_repo_info(github_url):
    try:
        parsed_url = urlparse(github_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            return None, "Geçersiz GitHub URL formatı"

        owner, repo = path_parts[:2]
        api_base = "https://api.github.com"
        repo_url = f"{api_base}/repos/{owner}/{repo}"
        readme_url = f"{api_base}/repos/{owner}/{repo}/readme"
        contents_url = f"{api_base}/repos/{owner}/{repo}/contents"

        repo_response = requests.get(repo_url)
        if repo_response.status_code != 200:
            return None, f"Repository bulunamadı: {repo_response.status_code}"
        repo_data = repo_response.json()

        readme_content = ""
        try:
            readme_response = requests.get(readme_url)
            if readme_response.status_code == 200:
                readme_data = readme_response.json()
                readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
        except:
            readme_content = "README bulunamadı"

        important_files = {}
        try:
            contents_response = requests.get(contents_url)
            if contents_response.status_code == 200:
                contents = contents_response.json()
                important_file_names = [
                    'requirements.txt', 'pyproject.toml', 'package.json', 'setup.py',
                    'main.py', 'app.py', 'index.py', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle'
                ]
                for file_info in contents:
                    file_name = file_info['name'].lower()
                    if file_name in important_file_names:
                        try:
                            file_response = requests.get(file_info['download_url'])
                            if file_response.status_code == 200:
                                important_files[file_name] = file_response.text[:2000]
                        except:
                            important_files[file_name] = "Dosya okunamadı"
        except:
            important_files = {}

        return {
            'owner': owner,
            'repo': repo,
            'name': repo_data.get('name', ''),
            'description': repo_data.get('description', ''),
            'language': repo_data.get('language', ''),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'topics': repo_data.get('topics', []),
            'readme': readme_content,
            'important_files': important_files,
            'created_at': repo_data.get('created_at', ''),
            'updated_at': repo_data.get('updated_at', ''),
            'homepage': repo_data.get('homepage', ''),
            'license': repo_data.get('license', {}).get('name', '') if repo_data.get('license') else ''
        }, None

    except Exception as e:
        return None, f"GitHub repository analizi hatası: {str(e)}"


def generate_github_analysis_prompt(repo_info):
    important_files_text = ""
    for filename, content in repo_info['important_files'].items():
        important_files_text += f"\n📄 {filename}:\n{content}\n"

    prompt = f"""
    Bu repository hakkında kısa analiz yap:
    
    📌 Repository: {repo_info['name']}
    👤 Owner: {repo_info['owner']}
    📝 Açıklama: {repo_info['description']}
    💻 Ana Dil: {repo_info['language']}
    ⭐ Yıldız: {repo_info['stars']}
    🍴 Fork: {repo_info['forks']}
    
    📖 README:
    {repo_info['readme'][:2000] if repo_info['readme'] else 'README bulunamadı'}
    
    Bu proje gerçekte ne yapıyor?
    Hangi teknolojileri kullanıyor?
    Ben ne için bu projeyi kullanmalıyım?
    Bana gerçekten faydalı olur mu?
    
    Kısa paragraflar halinde, akıcı bir şekilde cevap ver. Her başlık altında maksimum 2-3 cümle olsun. Madde madde yazma. Doğrudan analiz içeriğine başla.
    """
    return prompt
