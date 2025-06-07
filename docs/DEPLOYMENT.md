# Deployment Guide

This guide covers deploying the Bitcoin Arbitrage Monitor to run continuously on your homeserver using Docker.

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- Git installed

## 🚀 Quick Deployment

```bash
# 1. Install Docker and Docker Compose (if not already installed)
sudo apt update
sudo apt install docker.io docker-compose git
sudo usermod -aG docker $USER
# Log out and back in to apply group changes

# 2. Clone and deploy
git clone <your-repo-url>
cd exchange-price-slippage-arbitrage
./deploy.sh
```

That's it! The deployment script will:
- ✅ Check Docker installation
- ✅ Create necessary directories
- ✅ Help you configure environment variables
- ✅ Build and start the service
- ✅ Show you management commands

## ⚙️ Configuration

### Environment Variables

Edit `.env` file with your settings:

```bash
# Required
MIN_PROFIT_PERCENTAGE=0.1

# Optional API keys for enhanced features
KRAKEN_API_KEY=your_key_here
KRAKEN_SECRET_KEY=your_secret_here
COINMATE_API_KEY=your_key_here
COINMATE_SECRET_KEY=your_secret_here
COINMATE_CLIENT_ID=your_id_here

# Development
SANDBOX_MODE=true
```

### API Key Setup

1. **Kraken API**: Visit https://kraken.com/u/security/api
   - Create read-only key for monitoring
   - Enable "Query Funds" and "Query Open Orders" if needed

2. **Coinmate API**: Visit https://coinmate.io/api
   - Create API key with minimal permissions
   - Only enable "Account info" for monitoring

## 📊 Monitoring & Maintenance

### Essential Commands

```bash
# View live logs
docker-compose logs -f

# View recent logs
docker-compose logs --tail=50

# Restart service
docker-compose restart

# Stop service
docker-compose down

# Update and restart
git pull && docker-compose build && docker-compose up -d

# Check container status
docker-compose ps

# Access container shell
docker-compose exec arbitrage-monitor bash
```

### Log Management

Logs are automatically rotated using logrotate:

```bash
# Install logrotate config (optional - run once)
sudo cp monitoring/logrotate.conf /etc/logrotate.d/bitcoin-arbitrage

# Test logrotate
sudo logrotate -d /etc/logrotate.d/bitcoin-arbitrage
```

## 🔧 Health Monitoring

### Simple Health Check Script

```bash
#!/bin/bash
# health-check.sh

if docker-compose ps | grep -q "Up"; then
    echo "✅ Service is running"
    exit 0
else
    echo "❌ Service is down - restarting..."
    docker-compose up -d
    exit 1
fi
```

### Cron Job for Health Checks

```bash
# Add to crontab (crontab -e)
*/5 * * * * cd /path/to/your/project && ./health-check.sh >> logs/health.log 2>&1
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   docker-compose logs
   ```

2. **API connection errors**
   - Verify API keys in `.env`
   - Check network connectivity
   - Ensure exchange APIs are accessible

3. **High memory usage**
   - Check for memory leaks in logs
   - Restart service: `docker-compose restart`

4. **Permission errors**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER logs/
   ```

### Performance Tuning

**Resource Limits**: Edit `docker-compose.yml` to add resource constraints:

```yaml
services:
  arbitrage-monitor:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## 🔒 Security Considerations

1. **API Keys**
   - Use read-only keys when possible
   - Set IP restrictions on exchange APIs
   - Store keys securely in `.env` file

2. **Network Security**
   - Run behind firewall
   - Consider VPN for sensitive operations
   - Monitor outbound connections

3. **System Security**
   - Run as non-root user
   - Regular security updates
   - Monitor system logs

## 📈 Scaling & Optimization

1. **Multiple Exchanges**
   - Add new exchanges to `config.py`
   - Update `EXCHANGE_TRADING_PAIRS`

2. **Performance Monitoring**
   - Monitor CPU/memory usage
   - Track API response times
   - Log arbitrage opportunities

3. **Data Storage**
   - Consider logging to database
   - Implement data retention policies
   - Add backup strategies

## 🔄 Updates

### Automatic Updates

```bash
# Create update script in your project directory
cat > auto-update.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
git pull
docker-compose build
docker-compose up -d
EOF
chmod +x auto-update.sh

# Add to crontab for weekly updates
0 2 * * 0 /path/to/your/project/auto-update.sh >> logs/update.log 2>&1
```

### Manual Updates

```bash
# Simple update
git pull
docker-compose build
docker-compose up -d
```

## 📞 Support

If you encounter issues:

1. Check logs first
2. Verify configuration
3. Test API connectivity
4. Review system resources
5. Check for known issues in documentation