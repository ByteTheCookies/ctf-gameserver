FROM cake_cleanup_deps

# Copy cleanup script
COPY cleanup.sh /usr/local/bin/cleanup.sh
RUN chmod +x /usr/local/bin/cleanup.sh

# Copy cronjob
COPY cronjob /etc/crontabs/root

# Run cron in foreground
CMD ["crond", "-f", "-l", "2"]
