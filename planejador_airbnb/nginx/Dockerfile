FROM nginx:latest

# Remova a configuração padrão do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copie a nova configuração
COPY conf/default.conf /etc/nginx/conf.d/

# Crie diretórios necessários
RUN mkdir -p /var/www/certbot
