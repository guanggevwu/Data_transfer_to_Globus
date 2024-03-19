# Data_transfer_to_Globus

Compress a local directory to zip file and transfer it to a Globus Endpoint. GUI is available.

User instruction:

<ul>
<li>Directory Path and upload option. "Directory Path" can either be the folder or the folder that contains the subfolders you would like to upload. If it is the former, select "upload the entered folder". If it is the latter, select "upload the subfolders in the entered folder".</li>
<li>Connect to Globus. Click "Connect to Globus", a broswer window and a new program dialog window will open. In the broswer window, log in if it is required. Then copy the code, paste into the new program dialog window and click "Authorize". A common error here would be that someone else (who doesn't has the permission) has logged in Globus in the broswer. In this case, you will need to log out and log in your Globus account.</li>
<li>Compression and Upload. If "upload the entered folder" is selected, then the entered folder will be compressed and upload, even if the folder has been compressed or uploaded before. If "upload the subfolders in the entered folder" is selected, then only sub folders that haven't be compressed before will be compressed. Also if the a compressed file is detected in the destination endpoint, the upload request will be ignored.</li>
</ul>
