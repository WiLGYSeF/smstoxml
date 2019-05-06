# smstoxml
A tool to manipulate SMS and call backup XML files created by the app *SMS Backup & Restore*.
Allows you to backup emojis from messages and converts it to valid XML for viewing in browsers.

To view messages in a browser, make sure the `sms.xml` file is in the same directory as the SMS backup.

## Converting Exported XML Backup
Convert the emojis into valid XML, which can then be viewed on a browser:
```bash
python3 smstoxml.py sms.xml sms-converted.xml
```

## Importing Messages Back onto the Device
Converts the valid emoji characters back into invalid XML so the app can correctly restore the backup:
```bash
python3 smstoxml.py --revert sms-converted.xml sms-reverted.xml
```

## Listing the Contacts
Prints a list of the contacts in the backup file:
```bash
python3 smstoxml.py sms.xml --list
```

## Replacing/Normalizing Contact Numbers
Sometimes, the backup will contain different styles of numbers for the messages.

The number `+1-555-123-4567` may be found in the file in these formats for `John Doe`:
- +15551234567
- 15551234567
- 5551234567
- (555)1234567

To normalize them for easier parsing, viewing, filtering, etc.:
```bash
python3 smstoxml.py sms.xml sms-converted.xml --replace-number "John Doe" "+15551234567"
```

## Removing Messages
To delete messages from certain contacts:
```bash
python3 smstoxml.py sms.xml sms-converted.xml --filter-contact "John Doe" --filter-contact "Jane Doe" --filter-number "555123456" --remove-filtered
```

## Removing Calls (calls.xml)
To remove no-duration call entries from the call backup file:
```bash
python3 smstoxml.py calls.xml calls-new.xml --remove-no-duration
```

To remove calls from unknown numbers:
```bash
python3 smstoxml.py calls.xml calls-new.xml --filter-contact "(Unknown)" --remove-filtered
```

## Shrinking Image Sizes
If the backup file size is large, you can save space by shrinking images, or lowering the JPG quality.
Setting the width/height will scale the images to the specified maximum width/height.
```bash
python3 smstoxml.py sms.xml sms-optimized.xml --image-width 1024 --image-height 1024 --jpg-quality 80
```

Can also use the filter arguments to only change the images from certain contacts.
```bash
python3 smstoxml.py sms.xml sms-optimized.xml --image-width 1024 --jpg-quality 80 -f "John Doe"
```

## Extract Media
Extracts embedded media into a zip file. Can be used with image optimization arguments, which will be applied to the extracted media.
```bash
python3 smstoxml.py sms.xml --extract-media "media.zip"
```

Can also use the filter arguments to only export from certain contacts.
```bash
python3 smstoxml.py sms.xml --extract-media "media.zip" -f "John Doe"
```
