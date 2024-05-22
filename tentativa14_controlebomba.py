import time
import serial
import PySimpleGUI as sg
arduino=False
arduino_port="COM6"
final_command_line=['', '1000000000', '']
#original: 1000000000
def ajusting_type(string):
    number=string.replace(",", ".")
    return float(number)
def computing_speed(flow):
    speed=flow * 26.66666667
    speed=round(speed, 7)
    window["speed_result"].update(speed)
    return speed
def aplly_direction(open, close):
    if open==True:
        final_command_line[0]="o"
    elif close==True:
        final_command_line[0]="c"
    direction=final_command_line[2]
    visual_responses_main('p',1,direction)

def visual_responses_main(light, connection_message, status_message):
    if light=='g':
        window["led"].update(background_color="lime green")
    elif light=='r':
        window["led"].update(background_color="red")
    elif light=='y':
        window["led"].update(background_color='yellow')
    if connection_message==1:
        window["status_connection"].update("")
    elif connection_message==2:
        window["status_connection"].update("First, try connecting the syringe pump")
    elif connection_message==3:
        window["status_connection"].update("Enter commands first")
    elif connection_message==4:
        window["status_connection"].update("Speed too low for syringe pump")
    if status_message=='o':
        window["status_command"].update("Open Pump")
    elif status_message=='c':
        window["status_command"].update("Close Pump")
    elif status_message=='n':
        window["status_command"].update("Stop Pump")
    elif status_message=='e':
        window["status_command"].update("")

def time_responses(situation, start_active,exclusive_time):
    if situation=='f':
        send_command("n")
        window["timer_status"].update("Finished")
    if situation=='a':
        reading_main()
        window["timer_status"].update("Active")
        initial=time.time()
        limit=initial+time_information[1]
        while time.time()<limit:
            click, reading=window.read(timeout=1000*time_information[1])
            if click=="STOP1" or click=="STOP2" or click==" ":
                time_responses('f', start_active,exclusive_time)
                return True
            window['time'].update(time.ctime(time.time()))
    if situation=='s':
        send_command("n")
        window["timer_status"].update("Sleep")
        initial=time.time()
        limit=initial+time_information[2]
        while time.time()<limit:
            click, reading=window.read(timeout=1000*time_information[2])
            if click=="STOP1" or click=="STOP2" or click==" ":
                time_responses('f', start_active,exclusive_time)
                return True
    return False

def time_control(hours, minutes,start_active, time_information, exclusive_time):
    if exclusive_time[0]==True:
        time_information[0]=ajusting_type(time_information[0])
        time_information[1]=time_information[0]
        time_information[2]=time_information[0]
    else:
        for index in range(0,3,1):
            time_information[index]=ajusting_type(time_information[index])
    if hours==True:
        for index in range(0,3,1):
            time_information[index]=time_information[index] * 3600
    if minutes==True:
        for index in range(0,3,1):
            time_information[index]=time_information[index] * 60
    current_time=time.time()
    break_point=False
    limit_time=current_time+time_information[0]
    while current_time< limit_time:
        if start_active==True or exclusive_time[1]=="a":
            break_point=time_responses('a', start_active,exclusive_time)
            current_time=current_time+time_information[1]
        if start_active==False or exclusive_time[1]=='s':
            break_point=time_responses('s', start_active,exclusive_time)
            current_time=current_time+time_information[2]
        if break_point==True:
            break
        start_active= not start_active
    time_responses('f', start, exclusive_time)

def send_command(final_command_line):
    visual_responses_main('g',1,final_command_line[0])
    if final_command_line[0]=="n":
        arduino.write(final_command_line.encode())
        arduino.flush()
    else:
        command_phrase=""
        for item in final_command_line:
            command_phrase+=str(item)+" "
        command_phrase=command_phrase.strip()
        arduino.write(command_phrase.encode())
        arduino.flush()
        for index in range(0,3,2):
            final_command_line[index]=""

def reading_main():
    open_direction=reading["open_command"]
    close_direction=reading["close_command"]
    aplly_direction(open_direction, close_direction)
    received_flow=reading["received_flow"]
    if received_flow=='' or (open_direction==False and close_direction==False):
        visual_responses_main('y',3,'e')
        return
    flow=ajusting_type(received_flow)
    final_command_line[2]=computing_speed(flow)
    send_command(final_command_line)

def pairing():
    while True:
        try:
            arduino=serial.serial_for_url(arduino_port, 230400)
            if arduino.port!="COM6":
                visual_responses_main('r',1, 'e')
                return False
            else:
                window["led"].update(background_color="lime green")
                window["status_connection"].update("")
                visual_responses_main('g',1,'e')
                return arduino 
        except serial.SerialException or serial.PortNotOpenError or serial.InvalidPortError:
            visual_responses_main('r',1,'e')
            return False
        
tab1_layout=[
    [sg.Text("SINC:",font=("", 10, "bold")), sg.Canvas(size=(15, 15),background_color='light gray', key='led'), sg.Text("",key="status_connection")],
    [sg.Button("CONNECT", button_color="Gray")],
    [sg.Radio("Reverse", "direction", key="open_command", font=("", 10, "bold")), sg.Text("(Open)")],
    [sg.Radio("Foward", "direction", key="close_command", font=("", 10, "bold")), sg.Text("(Close)")],
    [sg.InputText(size=(15, 30), key="received_flow"), sg.Text("μL/min", font=("", 10, "bold"))],
    [sg.Button("START", button_color="Lime Green", key="START1"), sg.Button(button_text="STOP", button_color="Red", key='STOP1')],
    [sg.Text("Speed:"),sg.Text("", key='speed_result'),sg.Text("steps/sec", font=("", 10, "bold"))],
    [sg.Text("", key="status_command", font=("", 10, "bold"))],
]
tab2_layout=[
    [sg.Checkbox("Timer", default=False, key='use_timer')],
    [sg.Text("Total Time:  "), sg.InputText(key="total_time", size=(10, 20))], 
    [sg.Text("Active Time:"), sg.InputText(key="action_time", size=(10, 20))],
    [sg.Text("Sleep Time: "),sg.InputText(key="sleeping_time", size=(10, 20))],
    [sg.Radio("Hrs", "time",key="hours_time"), sg.Radio("Mns", "time",key="min_time"), sg.Radio("Secs", "time", key="secs_time")],
    [sg.Checkbox("Start Active", 'start',key="start_active")],
    [sg.Button("START", button_color="Lime Green", key='START2'), sg.Button("STOP", button_color="Red", key='STOP2')],
    [sg.Text("Timer Status:"), sg.Text("", key='timer_status', font=("", 10, "bold")), sg.Text("", key='time')],
]
layout=[ 
    [sg.TabGroup([[sg.Tab("Main", tab1_layout), sg.Tab("Timer", tab2_layout)]])],
]
window=sg.Window("Syringe Pump", layout, return_keyboard_events=True)
sg.theme_global("GrayGrayGray")

while True:
    click, reading=window.read()
    if click==sg.WIN_CLOSED or click=="Escape:27":
        break
    if click=="CONNECT":
        arduino=pairing()
    if click=="START1" or click=="START2" or click=="\r":
        if arduino==False:
            visual_responses_main('y',2,'p')
            continue
        use_checkbox=reading["use_timer"]
        if use_checkbox==True:
            exclusive_time=[False, 'o']
            total_time=reading["total_time"]
            active_time=reading["action_time"]
            sleep_time=reading["sleeping_time"]
            if (active_time=="" or active_time=="-") and (sleep_time=="" or sleep_time=="-"):
                exclusive_time[0]=True
            time_information=[total_time, active_time, sleep_time]
            hours=reading["hours_time"]
            minutes=reading['min_time']
            seconds=reading["secs_time"]
            if hours==False and minutes==False and seconds==False:
                visual_responses_main('y',3,'e')
                continue
            start_active=reading["start_active"]
            if start_active==True:
                start=True
                if exclusive_time==True:
                    exclusive_time[1]='a'
            else:
                start=False
                if exclusive_time==True:
                    exclusive_time[1]='s'
            time_control(hours, minutes,start, time_information, exclusive_time)
        else:
            reading_main()
    if click=="STOP1" or click=="STOP2" or click==" ":
        if arduino==False:
            visual_responses_main('y',2,'e')
            continue
        send_command("n")
if arduino !=False:
    arduino.close()
window.close()