# GreenBite

A sustainable recipe recommendation system that helps users make environmentally conscious food choices.

## Dataset Setup

Before running the application, you need to download the required datasets:

1. Download the datasets from [Google Drive](https://drive.google.com/drive/folders/1ZBMDaGu3kOSENX6grPEe-Ub5sz1Udl7D?usp=sharing)
   - `filtered_recipes_1m.csv.gz`
   - `Food_Product_Emissions.csv`

2. Place the downloaded files in the `datasets/` directory

## Deployment Instructions

### Frontend (Vercel)

1. Fork this repository
2. Sign up on [Vercel](https://vercel.com)
3. Import your forked repository
4. Select the `frontend` directory as the root directory
5. Add the following environment variable:
   - `REACT_APP_API_URL`: Your Render backend URL (you'll get this after deploying the backend)
6. Deploy!

### Backend (Render)

1. Sign up on [Render](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Set the following:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add the following environment variables:
   - `FLASK_ENV=production`
   - `FRONTEND_URL`: Your Vercel frontend URL (you'll get this after deploying the frontend)
6. Deploy!

### Dataset Storage

The datasets are stored using Git LFS (Large File Storage). To work with the datasets:

1. Install Git LFS: `git lfs install`
2. Clone the repository: `git clone https://github.com/yourusername/greenbite.git`
3. The datasets will be automatically downloaded when you clone

## Environment Variables

Create a `.env` file in the frontend directory with:
```
REACT_APP_API_URL=your-render-backend-url
``` 
