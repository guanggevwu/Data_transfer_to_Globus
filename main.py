import globus_sdk
import shutil
import os
from tkinter import *
from tkinter import ttk
import webbrowser
from threading import Thread
import time

class DataUpload:
    def __init__(self, root):
        self.count = 0
        with open("start_up.txt") as file:
            self.lines = file.readlines()
            self.start_up_path, self.CLIENT_ID, self.start_up_source_endpoint, self.start_up_destination_endpoint = [line.strip() for line in self.lines]
        root.title("Upload data to UM Data Den")
        s = ttk.Style()
        s.configure('Sty1.TLabelframe.Label', foreground="blue", font=('Times', 15))
        
        pad_widget = "0 0 0 10"
        frame1  = ttk.Labelframe(root, text='Data Information', padding=pad_widget, style='Sty1.TLabelframe')
        frame1.grid(column=0, row=0, sticky=(N, W, E, S))

        ttk.Label(frame1, text='Directory Path: ').grid(column=1, row=1, columnspan=1, sticky='W')
        self.dir_var = StringVar(value=self.start_up_path)
        dir_entry = ttk.Entry(frame1, width=80, textvariable=self.dir_var)
        dir_entry.grid(column=2, row=1, columnspan=3, sticky=(W))

        ttk.Label(frame1, text='Source Endpoint: ').grid(column=1, row=2, columnspan=1, sticky='')
        self.source_var = StringVar(value=self.start_up_source_endpoint)
        source_entry = ttk.Entry(frame1, width=20, textvariable=self.source_var)
        source_entry.grid(column=2, row=2, columnspan=1, sticky=(W))

        ttk.Label(frame1, text='Destination Endpoint: ').grid(column=3, row=2, columnspan=1, sticky='E')
        self.destination_var = StringVar(value=self.start_up_destination_endpoint)
        destinstion_entry = ttk.Entry(frame1, width=20, textvariable=self.destination_var, state="disabled")
        destinstion_entry.grid(column=4, row=2, columnspan=1, sticky=(W))

        frame2  = ttk.Labelframe(root, text='Operation', padding=pad_widget, style='Sty1.TLabelframe')
        frame2.grid(column=0, row=1, sticky=(N, W, E, S))
        frame2.grid_columnconfigure(0, weight=1)
        frame2.grid_columnconfigure(1, weight=1)

        self.b1 = ttk.Button(frame2, text="Connect to Globus", command=self.connect)
        self.b1.grid(column=0, row=0, columnspan=1, sticky=[W, E])
        self.b2 = ttk.Button(frame2, text="Compress and Upload", command=self.compression_and_upload)
        self.b2.grid(column=1, row=0, columnspan=1, sticky=[W, E])

        self.frame3  = ttk.Labelframe(root, text='Task Information', padding=pad_widget, style='Sty1.TLabelframe')
        self.frame3.grid(column=0, row=2, sticky=(N, W, E, S))


        self.t = Text(self.frame3, width = 70, height=10, wrap=WORD)
        self.t.grid(column=0, row=0, columnspan=1, sticky=W)
        self.t.insert(INSERT, "Started.\n")
        sb = ttk.Scrollbar(self.frame3,
                            orient='vertical',
                            command=self.t.yview)

        sb.grid(column=1, row=0, sticky=NS)
        self.t['yscrollcommand'] = sb.set
        self.t['state'] = 'disabled'

        self.status_label = ttk.Label(self.frame3, text="", foreground="red", cursor="hand2", font=('Times', 12, 'underline'))

        for child in [frame1.winfo_children()[childidx] for childidx in [0,1]]: 
            child.grid_configure(padx=[0,0], pady=3)  


        for child in [frame2.winfo_children()[childidx] for childidx in [0,1]]: 
            child.grid_configure(padx=[0,0], pady=3)  

        for child in [self.frame3.winfo_children()[childidx] for childidx in [0]]: 
            child.grid_configure(padx=[0,0], pady=3)  

    def insert_to_disabled(self, t, text):
        self.t['state'] = 'normal'
        self.t.insert(END, text)
        self.t['state'] = 'disabled'

    def connect(self):
        with open("start_up.txt", 'w') as file:
            self.lines[2] = self.source_var.get() + "\n"
            file.writelines(self.lines)
        self.insert_to_disabled(self.t, "Please copy the code returned from your browser and paste it to the popup window!\n")
        self.status_label.config(text="", foreground="black")

        self.ZEUS_app = ZEUSAPP(CLIENT_ID=self.CLIENT_ID)
        self.ZEUS_app.client.oauth2_start_flow(requested_scopes=self.ZEUS_app.scopes, refresh_tokens=True)
        self.authorize_url = self.ZEUS_app.client.oauth2_get_authorize_url()
        webbrowser.open_new(self.authorize_url)
        if  not(hasattr(self, "window1") and self.window1.winfo_exists()):
            self.window1 = NewWindow(self.verify)
        self.window1.title("connecting")


    def verify(self, code):

        token_response = self.ZEUS_app.client.oauth2_exchange_code_for_tokens(code)

        transfer_token = token_response.by_resource_server["transfer.api.globus.org"]
        group_token = token_response.by_resource_server["groups.api.globus.org"]

        # the refresh token and access token are often abbreviated as RT and AT
        transfer_rt = transfer_token["refresh_token"]
        transfer_at = transfer_token["access_token"]
        group_rt = group_token["refresh_token"]
        group_at = group_token["access_token"]
        expires_at_s = transfer_token["expires_at_seconds"] + 1

        authorizer_transfer = globus_sdk.RefreshTokenAuthorizer(
            transfer_rt, self.ZEUS_app.client, access_token=transfer_at, expires_at=expires_at_s
        )
        authorizer_group = globus_sdk.RefreshTokenAuthorizer(
            group_rt, self.ZEUS_app.client, access_token=group_at, expires_at=expires_at_s
        )
        self.ZEUS_app.ac = globus_sdk.AuthClient(authorizer=authorizer_transfer)
        self.ZEUS_app.tc = globus_sdk.TransferClient(authorizer=authorizer_transfer)
        self.ZEUS_app.gc = globus_sdk.GroupsClient(authorizer=authorizer_group)
        self.ZEUS_app.gm = globus_sdk.GroupsManager(self.ZEUS_app.gc)

        #use first search result
        self.ZEUS_app.source_endpoint_id = list(self.ZEUS_app.tc.endpoint_search(self.source_var.get()))[0]["id"]
        if not self.ZEUS_app.source_endpoint_id:
            self.insert_to_disabled(self.t, f"Can't reach source endpoint.\n")
            return
        self.ZEUS_app.destination_endpoint_id = list(self.ZEUS_app.tc.endpoint_search(self.destination_var.get()))[0]["id"]
        if not self.ZEUS_app.source_endpoint_id:
            self.insert_to_disabled(self.t, f"Can't reach destination endpoint.\n")
            return
        self.insert_to_disabled(self.t, "Connected to Globus successfully!\n")


    def compression_and_upload(self):
        with open("start_up.txt", 'w') as file:
            self.lines[0] = self.dir_var.get() + "\n"
            file.writelines(self.lines)
        self.directory_path = self.dir_var.get()
        if not os.path.exists(self.directory_path):
            self.insert_to_disabled(self.t, "Invalid directory path or file path. Please check again.\n")
            return
        self.dir_parts = self.directory_path.split(os.sep)

        def threaded_function(arg):
            shutil.make_archive(arg, 'zip', arg)
        thread = Thread(target = threaded_function, args = (self.directory_path, ))

        thread.start()
        self.monitor(thread)



    def monitor(self, thread):
        if self.count == 0:
            self.insert_to_disabled(self.t, f"Compressing.\n")
        self.count += 1
        if thread.is_alive():
            # check the thread every 100ms
            self.t['state'] = 'normal'
            self.t.delete("end -2 lines","end -1 lines") 
            self.t.insert("end",f"Compressing...Elapsed time: {self.count} s.\n")
            self.t['state'] = 'disabled'
            self.t.see("end")
            root.after(1000, lambda: self.monitor(thread))
        else:

            self.insert_to_disabled(self.t, "Compression finished.\n")
            self.count = 0

            # create a Transfer task consisting of one or more items
            task_data = globus_sdk.TransferData(
                source_endpoint=self.ZEUS_app.source_endpoint_id, destination_endpoint=self.ZEUS_app.destination_endpoint_id
            )
            task_data.add_item(
                "/"+(self.directory_path + ".zip").replace(":","").replace("\\", "/"),  # source
                os.path.join("/experimental_data", self.dir_parts[-2],self.dir_parts[-1],  self.dir_parts[-1] ).replace("\\", "/")+".zip",  # dest

            )

            # submit, getting back the task ID
            task_doc = self.ZEUS_app.tc.submit_transfer(task_data)
            task_id = task_doc["task_id"]
            self.insert_to_disabled(self.t, f"Submitted transfer. Task_id: {task_id}.\n")

            self.status_label.config(text="Check transfer progress")
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
        ttk.Label(newframe1, text="Copy the code from browser and paste it here: ").grid(row=0, column=0, columnspan=3)  

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
        
class ZEUSAPP:
    def __init__(self, CLIENT_ID,):
        self.CLIENT_ID = CLIENT_ID
        self.client = globus_sdk.NativeAppAuthClient(self.CLIENT_ID)
        self.scopes = ['urn:globus:auth:scope:transfer.api.globus.org:all', 'urn:globus:auth:scope:groups.api.globus.org:all']
        
root = Tk()
DataUpload(root)
root.mainloop()
