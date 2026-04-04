# Ubuntu Server Deployment Guide

These instructions are tailored specifically for your app, automatically setting up **Nginx, Gunicorn**, and creating a highly secure `.env` parameter block for domain whitelisting.

### 1. Push Files
First, push all these new generated deployment files to your github from your development computer:
```bash
git add .
git commit -m "Added deployment config"
git push
```

### 2. Connect to your new Server
Log in to your Ubuntu remote server containing the newly mapped IP address of `aalam-synak.edu.kg`. Make sure you are acting as the `ubuntu` standard user, placing your repository at `/home/ubuntu/Aalam-Synak`. If you clone to a different username, modify the paths accordingly in `deployment/` files.

### 3. Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/Nekono3/Aalam-Synak.git
cd Aalam-Synak
```

### 4. Run Automagic Deployment
Run the script I wrote which handles all networking and daemon monitoring setups entirely automatically:
```bash
bash deployment/deploy.sh
```

### 5. Secure with HTTPS
Once the script successfully executes, optionally bind it with SSL to serve safely over HTTPS:
```bash
sudo certbot --nginx -d aalam-synak.edu.kg -d www.aalam-synak.edu.kg
```
