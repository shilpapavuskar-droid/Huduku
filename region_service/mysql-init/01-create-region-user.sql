CREATE USER 'region_user'@'%' IDENTIFIED BY 'rootpass';
GRANT ALL PRIVILEGES ON regiondb.* TO 'region_user'@'%';
FLUSH PRIVILEGES;