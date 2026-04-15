sudo nano /usr/local/bin/voltage_led_warning.py
sudo chmod +x /usr/local/bin/voltage_led_warning.py
sudo nano /usr/local/bin/voltage_led_warning.conf
sudo nano /etc/systemd/system/voltage-led.service
sudo systemctl daemon-reload
sudo systemctl enable voltage-led
sudo systemctl start voltage-led
sudo systemctl status voltage-led