# simple QR-Code generator using Python Tkinter
from tkinter import *
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
from time import strftime
import pyqrcode as qr
import fontawesome as aw

# create a basic window
window = Tk()
window.title("PyQR-HVD")
window['bg'] = "white"
window.attributes("-top", 1)
window.iconbitmap("logo.ico")
window.geometry("300x430")
window.resizable(width=False, height=True)


def reload():
    try:
        window.bind("<Return>", genQR)
    except EXCEPTION:
        window.update()
    else:
        window.update_idletasks()


def genQR():
    try:
        link = var.get()
        decode = qr.create(link)
        file_types = [("PNG", "*.png"), ("SVG", "*.svg")]
        save_file = filedialog.asksaveasfile(filetypes=file_types, defaultextension=file_types)
        file_name = save_file.name
        if "svg" in file_name:
            decode.svg(file_name, background="white", scale=20)
        else:
            decode.png(file_name, scale=12)
        img1 = Image.open(file_name)
        img1 = img1.resize((200, 200), Image.ANTIALIAS)
        img1 = ImageTk.PhotoImage(img1)
        preview['image'] = img1
        preview.image = img1
        window.bind("<Return>", genQR)

        # get the information of the content
        date = strftime("%d-%m-%Y")
        time = strftime("%H : %M : %S %p")

        r = f"{'=='*20}\nData: {link}\nFile: {file_name}\nDate: {date}\nTime: {time}\n"

        # store the information in file
        f = open("info.txt", "a")
        f.write(r)
        f.close()

    except Exception as e:
        messagebox.showerror("Error Exception", e)


# create a placeholder for user input with input space
placeHolder = Label(window, text="Enter URL/data to Encode", font=("Arial", 11, "bold"),
                    bg="white")

# create an input space for data
var = StringVar()
data = Entry(window, textvariable=var, font=("Arial", 11, "bold"),
             width=30, relief="solid", justify="center")

# create a frame for preview of generated QR-Code
frame = LabelFrame(window, width=30, text="Preview - QR-Code", font=("Arial", 11, "bold"),
                   bg="white", relief="solid", labelanchor="n")

# load image
image = Image.open("logo.png")
image = image.resize((120, 120), Image.ANTIALIAS)
img = ImageTk.PhotoImage(image)

# display the loaded image in the preview section
preview = Label(frame, bg="white", image=img)

# create another frame for buttons
btn_frame = Frame(window, bg="white")

# create a button to generate QR-Code
generate = Button(btn_frame, text=f"{aw.icons['check']} Generate", font=('Arial', 11, "bold"), bg="white",
                  relief="solid", command=genQR)

# create a button to refresh the image of QR-Code
refresh = Button(btn_frame, text=f"{aw.icons['redo-alt']} Refresh", font=('Arial', 11, "bold"), bg="white",
                 relief="solid", command=reload)

# place the widgets according to the design
placeHolder.pack(side="top")
data.pack(side="top", padx=20, pady=12, fill="x")
frame.pack(side="top", padx=20, pady=5, expand=True, fill="both")
preview.pack(side="top", padx=5, pady=5, expand=True)
btn_frame.pack(side="top", expand=True, fill="both", padx=15)
generate.pack(side="left", expand=True, fill="x", padx=5, pady=5)
refresh.pack(side="right", expand=True, fill="x", padx=5, pady=5)

window.mainloop()
