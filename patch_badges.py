import re

with open('README.md', 'r') as f:
    content = f.read()

# The new HTML-friendly markdown to use for badges
new_badges_section = """### 🏅 Certifications & Badges
- **Google Cloud Platform (GCP) Verified Skills:**
  <br/>
  <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
    <a href="https://www.credly.com/badges/87703a7a-94d9-4ba0-8586-2e8a1350e152/public_url" target="_blank">
      <img src="https://images.credly.com/images/1dbef1bd-cdb0-40e1-bff4-8200448c3161/linkedin_thumb_blob" alt="Develop GenAI Apps with Gemini and Streamlit Skill Badge" width="150" />
    </a>
    <a href="https://www.credly.com/badges/e66b66dd-e747-424b-b022-62f2db28eb89/public_url" target="_blank">
      <img src="https://images.credly.com/images/eea11cba-2a98-4bbe-bad2-447878dd34a2/linkedin_thumb_image.png" alt="Implement Load Balancing on Compute Engine Skill Badge" width="150" />
    </a>
    <a href="https://www.credly.com/badges/32b54f0b-ba99-4655-b40a-15d3d7883d69/public_url" target="_blank">
      <img src="https://images.credly.com/images/68756311-9319-4eeb-a2b7-76defc8dd8a2/linkedin_thumb_image.png" alt="Prepare Data for ML APIs on Google Cloud Skill Badge" width="150" />
    </a>
    <a href="https://www.credly.com/badges/7d83a617-ba0b-4e45-9b8a-a70ceef6f4c3/public_url" target="_blank">
      <img src="https://images.credly.com/images/cef82b2e-970a-4318-8e59-c3e26b7f5c19/linkedin_thumb_image.png" alt="Prompt Design in Vertex AI Skill Badge" width="150" />
    </a>
    <a href="https://www.credly.com/badges/5fe1a562-e4c2-4ab2-95e8-71c96bbf0132/public_url" target="_blank">
      <img src="https://images.credly.com/images/42326d44-14ff-4eda-b9c5-7d8f12919253/linkedin_thumb_image.png" alt="Set Up an App Dev Environment on Google Cloud Skill Badge" width="150" />
    </a>
  </div>

"""

# Regex to match the current Certifications & Badges section and replace it
content = re.sub(r'### 🏅 Certifications & Badges.*?### 🚀', new_badges_section + '### 🚀', content, flags=re.DOTALL)

with open('README.md', 'w') as f:
    f.write(content)
