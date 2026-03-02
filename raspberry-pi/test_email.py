import apprise
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

a = apprise.Apprise()
# Use mailtos:// format with user:password@host and proper query params
a.add('mailtos://friends%40marcjones.co.uk:rwuaeolplrykqurc@smtp.gmail.com:587/?from=friends@marcjones.co.uk&to=friends@marcjones.co.uk')

result = a.notify(
    title='Test from ChangeDetection.io',
    body='This is a test email from your Raspberry Pi website monitor.\n\nIf you receive this, email notifications are working!\n\nMonitoring:\n- Queen Marys High School Admissions\n- Sandwell Academy\n- Sandwell Council School Admissions'
)

print('Email sent successfully!' if result else 'Email failed to send')
