import tkinter as tk
from tkinter import ttk
import threading
import time
import win32gui
import win32con
import win32api
import json
import os

class TibiaAutomation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tibia Auto Hotkey v2 - Global Background")
        self.root.geometry("900x650")
        self.root.configure(bg='#1e1e1e')
        
        # Dicionário para armazenar threads de automação
        self.automation_threads = {}
        self.running_automations = {}
        self.hotkey_listeners = {}
        
        # Sistema de pausa inteligente (pausa magias se detectar CTRL/SHIFT/ALT pressionados)
        self.pause_while_typing = {}  # {hwnd: pause_until_time}
        self.pause_duration = 0.5  # Pausa por 500ms quando detectar modificadores
        
        # Configuração de hotkeys (global)
        self.hotkey_config = [
            {'key': 'f7', 'delay': '200', 'enabled': True},
            {'key': 'f8', 'delay': '200', 'enabled': True},
            {'key': 'f9', 'delay': '200', 'enabled': True},
            {'key': 'f10', 'delay': '200', 'enabled': True},
            {'key': 'space', 'delay': '1000', 'enabled': True},
            {'key': 'f11', 'delay': '10000', 'enabled': True},
        ]
        
        self.setup_ui()
        self.start_keyboard_monitor()
        
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1e1e1e', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title = tk.Label(main_frame, text="🎮 Tibia Auto Hotkey (Global Background)", 
                        font=('Arial', 16, 'bold'), bg='#1e1e1e', fg='#00ff00')
        title.pack(pady=(0, 10))
        
        # Info
        info = tk.Label(main_frame, text="⚠️ Hotkeys são capturadas globalmente. Aperte as teclas em qualquer lugar!", 
                        font=('Arial', 9), bg='#1e1e1e', fg='#ffaa00')
        info.pack(pady=(0, 15))
        
        # Frame de configuração de hotkeys
        hotkey_frame = tk.LabelFrame(main_frame, text="⌨️ Configuração de Hotkeys", 
                                     bg='#2d2d2d', fg='#ffffff', 
                                     font=('Arial', 11, 'bold'), padx=15, pady=15)
        hotkey_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Cabeçalho da tabela
        header_frame = tk.Frame(hotkey_frame, bg='#2d2d2d')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="Ativo", bg='#2d2d2d', fg='#aaaaaa', 
                font=('Arial', 9, 'bold'), width=6).pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="Tecla", bg='#2d2d2d', fg='#aaaaaa', 
                font=('Arial', 9, 'bold'), width=10).pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="Delay (ms)", bg='#2d2d2d', fg='#aaaaaa', 
                font=('Arial', 9, 'bold'), width=12).pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="Status", bg='#2d2d2d', fg='#aaaaaa', 
                font=('Arial', 9, 'bold'), width=15).pack(side=tk.LEFT, padx=5)
        
        # Lista de hotkeys
        self.hotkey_widgets = []
        for i, config in enumerate(self.hotkey_config):
            self.create_hotkey_row(hotkey_frame, i, config)
        
        # Botão adicionar hotkey
        add_btn = tk.Button(hotkey_frame, text="➕ Adicionar Hotkey", 
                           command=self.add_hotkey,
                           bg='#0d7377', fg='#ffffff', relief=tk.FLAT,
                           font=('Arial', 9, 'bold'), cursor='hand2')
        add_btn.pack(pady=(10, 0))
        
        # Botão atualizar janelas
        refresh_btn = tk.Button(main_frame, text="🔄 Atualizar Janelas Tibia", 
                               command=self.refresh_windows,
                               bg='#0d7377', fg='#ffffff', relief=tk.FLAT,
                               font=('Arial', 10, 'bold'), cursor='hand2')
        refresh_btn.pack(pady=(0, 10))
        
        # Frame de janelas (scrollable)
        canvas_frame = tk.Frame(main_frame, bg='#1e1e1e')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg='#1e1e1e', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.windows_frame = tk.Frame(canvas, bg='#1e1e1e')
        
        self.windows_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.windows_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Carregar janelas inicialmente
        self.refresh_windows()
    
    def create_hotkey_row(self, parent, index, config):
        """Cria uma linha de configuração de hotkey"""
        row_frame = tk.Frame(parent, bg='#3d3d3d', padx=10, pady=8)
        row_frame.pack(fill=tk.X, pady=3)
        
        # Checkbox ativo
        enabled_var = tk.BooleanVar(value=config['enabled'])
        check = tk.Checkbutton(row_frame, variable=enabled_var, bg='#3d3d3d', 
                              activebackground='#3d3d3d', selectcolor='#2d2d2d',
                              command=lambda: self.update_hotkey_enabled(index, enabled_var.get()))
        check.pack(side=tk.LEFT, padx=(5, 15))
        
        # Entry tecla
        key_var = tk.StringVar(value=config['key'])
        key_entry = tk.Entry(row_frame, textvariable=key_var, width=12,
                            bg='#2d2d2d', fg='#ffffff', insertbackground='#ffffff',
                            relief=tk.FLAT, font=('Arial', 10))
        key_entry.pack(side=tk.LEFT, padx=5)
        key_entry.bind('<FocusOut>', lambda e: self.update_hotkey_key(index, key_var.get()))
        
        # Entry delay
        delay_var = tk.StringVar(value=config['delay'])
        delay_entry = tk.Entry(row_frame, textvariable=delay_var, width=10,
                              bg='#2d2d2d', fg='#ffffff', insertbackground='#ffffff',
                              relief=tk.FLAT, font=('Arial', 10))
        delay_entry.pack(side=tk.LEFT, padx=5)
        delay_entry.bind('<FocusOut>', lambda e: self.update_hotkey_delay(index, delay_var.get()))
        
        # Label status
        status_var = tk.StringVar(value="Aguardando...")
        status_label = tk.Label(row_frame, textvariable=status_var, bg='#3d3d3d', 
                               fg='#888888', font=('Arial', 9), width=15)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Botão remover
        remove_btn = tk.Button(row_frame, text="🗑️", command=lambda: self.remove_hotkey(index),
                              bg='#e74c3c', fg='#ffffff', relief=tk.FLAT,
                              font=('Arial', 10), cursor='hand2', width=3)
        remove_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        self.hotkey_widgets.append({
            'frame': row_frame,
            'enabled_var': enabled_var,
            'key_var': key_var,
            'delay_var': delay_var,
            'status_var': status_var
        })
    
    def update_hotkey_enabled(self, index, value):
        """Atualiza se a hotkey está ativa"""
        if index < len(self.hotkey_config):
            self.hotkey_config[index]['enabled'] = value
    
    def update_hotkey_key(self, index, value):
        """Atualiza a tecla da hotkey"""
        if index < len(self.hotkey_config):
            self.hotkey_config[index]['key'] = value
    
    def update_hotkey_delay(self, index, value):
        """Atualiza o delay da hotkey"""
        if index < len(self.hotkey_config):
            try:
                int(value)
                self.hotkey_config[index]['delay'] = value
            except ValueError:
                self.hotkey_config[index]['delay'] = '100'
    
    def add_hotkey(self):
        """Adiciona uma nova hotkey"""
        new_config = {'key': 'f1', 'delay': '100', 'enabled': True}
        self.hotkey_config.append(new_config)
        
        hotkey_frame = None
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.LabelFrame) and "Hotkeys" in child.cget("text"):
                        hotkey_frame = child
                        break
        
        if hotkey_frame:
            add_button = hotkey_frame.winfo_children()[-1]
            add_button.pack_forget()
            self.create_hotkey_row(hotkey_frame, len(self.hotkey_config) - 1, new_config)
            add_button.pack(pady=(10, 0))
    
    def remove_hotkey(self, index):
        """Remove uma hotkey"""
        if len(self.hotkey_config) > 1 and index < len(self.hotkey_config):
            self.hotkey_config.pop(index)
            self.hotkey_widgets[index]['frame'].destroy()
            self.hotkey_widgets.pop(index)
    
    def get_tibia_windows(self):
        """Encontra todas as janelas do Tibia abertas"""
        windows = []
        
        def callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Tibia -" in title:
                    windows_list.append((hwnd, title))
            return True
        
        win32gui.EnumWindows(callback, windows)
        return windows
    
    def refresh_windows(self):
        """Atualiza a lista de janelas do Tibia"""
        for widget in self.windows_frame.winfo_children():
            widget.destroy()
        
        windows = self.get_tibia_windows()
        
        if not windows:
            no_window_label = tk.Label(self.windows_frame, 
                                      text="❌ Nenhuma janela do Tibia encontrada",
                                      bg='#1e1e1e', fg='#ff6b6b', 
                                      font=('Arial', 11))
            no_window_label.pack(pady=20)
        else:
            for hwnd, title in windows:
                self.create_window_control(hwnd, title)
    
    def create_window_control(self, hwnd, title):
        """Cria controle para uma janela específica"""
        frame = tk.Frame(self.windows_frame, bg='#2d2d2d', padx=15, pady=12)
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        title_label = tk.Label(frame, text=title, bg='#2d2d2d', 
                              fg='#ffffff', font=('Arial', 11, 'bold'))
        title_label.pack(anchor=tk.W)
        
        controls = tk.Frame(frame, bg='#2d2d2d')
        controls.pack(fill=tk.X, pady=(8, 0))
        
        status_var = tk.StringVar(value="⚫ Parado")
        status_label = tk.Label(controls, textvariable=status_var, 
                               bg='#2d2d2d', fg='#888888', font=('Arial', 9))
        status_label.pack(side=tk.LEFT, padx=(0, 15))
        
        start_btn = tk.Button(controls, text="▶ Start", 
                             command=lambda: self.start_automation(hwnd, status_var, start_btn, stop_btn),
                             bg='#2ecc71', fg='#ffffff', relief=tk.FLAT,
                             font=('Arial', 9, 'bold'), cursor='hand2', width=8)
        start_btn.pack(side=tk.LEFT, padx=2)
        
        stop_btn = tk.Button(controls, text="⬛ Stop", 
                            command=lambda: self.stop_automation(hwnd, status_var, start_btn, stop_btn),
                            bg='#e74c3c', fg='#ffffff', relief=tk.FLAT,
                            font=('Arial', 9, 'bold'), cursor='hand2', width=8,
                            state=tk.DISABLED)
        stop_btn.pack(side=tk.LEFT, padx=2)
    
    def send_key_to_window(self, hwnd, key):
        """Envia uma tecla para Tibia usando PostMessage (forma simples e confiável)"""
        key_map = {
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
            'space': win32con.VK_SPACE,
            'f1': win32con.VK_F1, 'f2': win32con.VK_F2, 'f3': win32con.VK_F3,
            'f4': win32con.VK_F4, 'f5': win32con.VK_F5, 'f6': win32con.VK_F6,
            'f7': win32con.VK_F7, 'f8': win32con.VK_F8, 'f9': win32con.VK_F9,
            'f10': win32con.VK_F10, 'f11': win32con.VK_F11, 'f12': win32con.VK_F12,
            'enter': win32con.VK_RETURN, 'tab': win32con.VK_TAB,
            'shift': win32con.VK_SHIFT, 'ctrl': win32con.VK_CONTROL,
            'alt': win32con.VK_MENU
        }
        
        key_lower = key.lower()
        
        if len(key) == 1 and key.isalpha():
            vk_code = ord(key.upper())
        else:
            vk_code = key_map.get(key_lower)
        
        if vk_code:
            try:
                # PostMessage simples - envia a tecla apenas para Tibia
                scan_code = win32api.MapVirtualKey(vk_code, 0)
                lParam_down = (1) | (scan_code << 16) | (0 << 24)
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, lParam_down)
                time.sleep(0.03)
                lParam_up = (1) | (scan_code << 16) | (1 << 30) | (1 << 31)
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, lParam_up)
                
            except Exception as e:
                print(f"Erro ao enviar tecla {key}: {e}")
    
    def hotkey_loop(self, hwnd, config):
        """Loop independente para cada hotkey com seu próprio delay"""
        while self.running_automations.get(hwnd, False):
            try:
                if not win32gui.IsWindow(hwnd):
                    break
                
                # Verificar se está em pausa (digitando/usando modificadores)
                if hwnd in self.pause_while_typing:
                    pause_until = self.pause_while_typing[hwnd]
                    if time.time() < pause_until:
                        # Ainda está em pausa, aguardar sem enviar magia
                        time.sleep(0.05)
                        continue
                    else:
                        # Pausa expirou, remover entrada
                        del self.pause_while_typing[hwnd]
                
                if config['enabled']:
                    self.send_key_to_window(hwnd, config['key'])
                    delay = float(config['delay']) / 1000.0
                    time.sleep(delay)
            
            except Exception as e:
                print(f"Erro no hotkey {config['key']}: {e}")
                break
            
            except Exception as e:
                print(f"Erro no hotkey {config['key']}: {e}")
                break
    
    def automation_loop(self, hwnd):
        """Loop principal que gerencia threads independentes para cada hotkey"""
        hotkey_threads = {}
        
        try:
            for i, config in enumerate(self.hotkey_config):
                thread = threading.Thread(
                    target=self.hotkey_loop, 
                    args=(hwnd, config), 
                    daemon=True,
                    name=f"hotkey-{config['key']}-{hwnd}"
                )
                hotkey_threads[i] = thread
                thread.start()
            
            while self.running_automations.get(hwnd, False):
                if not win32gui.IsWindow(hwnd):
                    break
                time.sleep(0.1)
        
        except Exception as e:
            print(f"Erro na automação: {e}")
    
    def start_automation(self, hwnd, status_var, start_btn, stop_btn):
        """Inicia automação para uma janela"""
        if hwnd in self.running_automations and self.running_automations[hwnd]:
            return
        
        self.running_automations[hwnd] = True
        status_var.set("🟢 Rodando")
        start_btn.config(state=tk.DISABLED)
        stop_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=self.automation_loop, args=(hwnd,), daemon=True)
        self.automation_threads[hwnd] = thread
        thread.start()
    
    def stop_automation(self, hwnd, status_var, start_btn, stop_btn):
        """Para automação para uma janela"""
        self.running_automations[hwnd] = False
        status_var.set("⚫ Parado")
        start_btn.config(state=tk.NORMAL)
        stop_btn.config(state=tk.DISABLED)
    
    def start_keyboard_monitor(self):
        """Inicia monitoramento de teclado em background para detectar digitação"""
        def monitor_keyboard():
            while True:
                try:
                    # Verificar se CTRL, SHIFT ou ALT estão pressionados
                    import ctypes
                    ctrl = ctypes.windll.user32.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000
                    shift = ctypes.windll.user32.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000
                    alt = ctypes.windll.user32.GetAsyncKeyState(win32con.VK_MENU) & 0x8000
                    
                    if ctrl or shift or alt:
                        # Se algum modificador foi detectado, pausar TODAS as automações por um tempo
                        current_time = time.time()
                        for hwnd in list(self.running_automations.keys()):
                            if self.running_automations.get(hwnd, False):
                                self.pause_while_typing[hwnd] = current_time + self.pause_duration
                    
                    time.sleep(0.05)  # Verificar 20x por segundo
                
                except Exception as e:
                    time.sleep(0.1)
        
        # Iniciar monitor em thread daemon
        monitor_thread = threading.Thread(target=monitor_keyboard, daemon=True)
        monitor_thread.start()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TibiaAutomation()
    app.run()
