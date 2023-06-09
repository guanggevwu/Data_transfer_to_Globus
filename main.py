import globus_sdk
import shutil
import os
from tkinter import *
from tkinter import ttk
import webbrowser


    
class DataUpload:
    def __init__(self, root):
        with open("start_up.txt") as file:
            self.directory_path, self.CLIENT_ID, self.endpoint_id = [f.strip() for f in list(file)]
        self.dir_parts = self.directory_path.split(os.sep)
        root.title("Upload data to UM Data Den")
        s = ttk.Style()
        s.configure('Sty1.TLabelframe.Label', foreground="blue", font=('Times', 15))
        
        pad_widget = "0 0 0 10"
        frame1  = ttk.Labelframe(root, text='Data information', padding=pad_widget, style='Sty1.TLabelframe')

        frame1.grid(column=0, row=0, sticky=(N, W, E, S))

        ttk.Label(frame1, text='Directory Path: ').grid(column=1, row=1, columnspan=1, sticky=W)
        self.dir_var = StringVar(value=self.directory_path)
        dir_entry = ttk.Entry(frame1, width=80, textvariable=self.dir_var)
        dir_entry.grid(column=2, row=1, columnspan=1, sticky=(W, E))


        frame2  = ttk.Labelframe(root, text='Operation', padding=pad_widget, style='Sty1.TLabelframe')
        frame2.grid(column=0, row=1, sticky=(N, W, E, S))
        frame2.grid_columnconfigure(0, weight=1)
        frame2.grid_columnconfigure(1, weight=1)

        # frame2.grid_rowconfigure(0, weight=1)
        self.b1 = ttk.Button(frame2, text="Connect to Globus", command=self.connect)
        self.b1.grid(column=0, row=0, columnspan=1, sticky=[W, E])
        self.b2 = ttk.Button(frame2, text="Compress and Upload", command=self.compression_and_upload)
        self.b2.grid(column=1, row=0, columnspan=1, sticky=[W, E])

        self.task_var = StringVar()
        self.frame3  = ttk.Labelframe(root, text='Task information', padding=pad_widget, style='Sty1.TLabelframe')
        self.frame3.grid(column=0, row=2, sticky=(N, W, E, S))
        self.message_label = ttk.Label(self.frame3, textvariable = self.task_var)
        self.message_label.grid(column=0, row=0, columnspan=1, sticky=W)

        self.status_label = ttk.Label(self.frame3, text="", foreground="red", cursor="hand2", font=('Times', 12, 'underline'))

        for child in [frame1.winfo_children()[childidx] for childidx in [0,1]]: 
            child.grid_configure(padx=[0,0], pady=3)  

        for child in [frame2.winfo_children()[childidx] for childidx in [0,1]]: 
            child.grid_configure(padx=[0,0], pady=3)  

        for child in [self.frame3.winfo_children()[childidx] for childidx in [0]]: 
            child.grid_configure(padx=[0,0], pady=3)  

    def connect(self):
        self.task_var.set("Please enter the code to the popup window!")
        self.status_label.config(text="")

        self.ZEUS_endpoint = ZEUSEndpoint(CLIENT_ID=self.CLIENT_ID, endpoint_id=self.endpoint_id)
        self.ZEUS_endpoint.client.oauth2_start_flow(requested_scopes=self.ZEUS_endpoint.scopes, refresh_tokens=True)
        self.authorize_url = self.ZEUS_endpoint.client.oauth2_get_authorize_url()
        webbrowser.open_new(self.authorize_url)
        self.window1 = NewWindow(self.verify)
        # self.window1.overrideredirect(True)
        self.window1.title("connecting")

        # print(f"Please go to this URL and login:\n\n{self.authorize_url}\n")

    def verify(self, code):

        token_response = self.ZEUS_endpoint.client.oauth2_exchange_code_for_tokens(code)

        transfer_token = token_response.by_resource_server["transfer.api.globus.org"]
        group_token = token_response.by_resource_server["groups.api.globus.org"]

        # the refresh token and access token are often abbreviated as RT and AT
        transfer_rt = transfer_token["refresh_token"]
        transfer_at = transfer_token["access_token"]
        group_rt = group_token["refresh_token"]
        group_at = group_token["access_token"]
        expires_at_s = transfer_token["expires_at_seconds"] + 1

        authorizer_transfer = globus_sdk.RefreshTokenAuthorizer(
            transfer_rt, self.ZEUS_endpoint.client, access_token=transfer_at, expires_at=expires_at_s
        )
        authorizer_group = globus_sdk.RefreshTokenAuthorizer(
            group_rt, self.ZEUS_endpoint.client, access_token=group_at, expires_at=expires_at_s
        )
        self.ZEUS_endpoint.ac = globus_sdk.AuthClient(authorizer=authorizer_transfer)
        self.ZEUS_endpoint.tc = globus_sdk.TransferClient(authorizer=authorizer_transfer)
        self.ZEUS_endpoint.gc = globus_sdk.GroupsClient(authorizer=authorizer_group)
        self.ZEUS_endpoint.gm = globus_sdk.GroupsManager(self.ZEUS_endpoint.gc)
        
        self.task_var.set(f"Connected to Globus successfully!")
        self.message_label.config(foreground="green")

    def compression_and_upload(self):
        with open("start_up.txt", 'w') as file:
            file.write(self.dir_var.get())
        shutil.make_archive(self.directory_path, 'zip', self.directory_path)


        # for x in self.ZEUS_endpoint.tc.endpoint_search("2006client"):
        #     print("Endpoint ID: {}".format(x["display_name"]))

        #use first search result
        source_endpoint_id = list(self.ZEUS_endpoint.tc.endpoint_search("2006client"))[0]["id"]


        # create a Transfer task consisting of one or more items
        task_data = globus_sdk.TransferData(
            source_endpoint=source_endpoint_id, destination_endpoint=self.ZEUS_endpoint.endpoint_id
        )
        task_data.add_item(
            "/"+(self.directory_path + ".zip").replace(":","").replace("\\", "/"),  # source
            os.path.join("/experimental_data", self.dir_parts[-3],self.dir_parts[-2],  self.dir_parts[-3] ).replace("\\", "/")+".zip",  # dest

        )

        # submit, getting back the task ID
        task_doc = self.ZEUS_endpoint.tc.submit_transfer(task_data)
        task_id = task_doc["task_id"]
        self.task_var.set(f"Submitted transfer. Task_id={task_id}")

        self.status_label.config(text="check transfer progress")
        self.status_label.grid(column=0, row=1, columnspan=1, sticky=W)      
        self.status_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://app.globus.org/activity"))

class NewWindow(Toplevel):
    def __init__(self, verify):
        super().__init__(master = root)
        self.verify = verify


        newframe1 = ttk.Frame(self)
        newframe1.grid(column=0, row=0, columnspan=1, sticky=(N, W, E, S))
        newframe1.grid_columnconfigure(0, weight=1)
        newframe1.grid_columnconfigure(1, weight=1)
        newframe1.grid_columnconfigure(2, weight=1)
        ttk.Label(newframe1, text="Type anything in the broswer and click \"allow\". Enter the code copied from broswer: ").grid(row=0, column=0, columnspan=3)  

        self.code_input_var = StringVar()
        code_entry = ttk.Entry(newframe1, width=50, textvariable=self.code_input_var)
        code_entry.grid(row=1, column=0, columnspan=3, sticky=(W, E))

        self.b3 = ttk.Button(newframe1, text="Authorize", command=self.submit_code)
        self.b3.grid(row=2, column=1, columnspan=1, sticky=[W,E])

        for child in newframe1.winfo_children() : 
            child.grid_configure(padx=[0,0], pady=5)  

    def submit_code(self):
        self.verify(self.code_input_var.get())
        self.destroy()
        
class ZEUSEndpoint:
    def __init__(self, CLIENT_ID, endpoint_id):
        self.CLIENT_ID = CLIENT_ID
        self.endpoint_id = endpoint_id
        self.client = globus_sdk.NativeAppAuthClient(self.CLIENT_ID)
        self.scopes = ['urn:globus:auth:scope:transfer.api.globus.org:all', 'urn:globus:auth:scope:groups.api.globus.org:all']
        
root = Tk()
DataUpload(root)
root.mainloop()
