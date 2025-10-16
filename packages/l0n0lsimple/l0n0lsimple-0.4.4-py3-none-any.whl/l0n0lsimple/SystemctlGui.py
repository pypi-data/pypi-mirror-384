#!/usr/bin/env python3
# 文件名：ubuntu_service_manager.py

import subprocess
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog, simpledialog
import shutil
import os

# —— 工具函数 —— #


def run_cmd(cmd):
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, err = proc.communicate()
        return out, err, proc.returncode
    except Exception as e:
        return "", str(e), 1


def list_services():
    cmd = ["systemctl", "list-units", "--type=service",
           "--all", "--no-pager", "--no-legend"]
    out, err, code = run_cmd(cmd)
    services = []
    if code != 0:
        return services, err
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) >= 5 and parts[0].endswith(".service"):
            name, load, active, sub, desc = parts
            services.append((name, load, active, sub, desc))
    return services, ""


def service_status(name):
    out, err, code = run_cmd(["systemctl", "status", name, "--no-pager"])
    return out if code == 0 else (err or out)


def journal_logs(name, lines=50):
    out, err, code = run_cmd(
        ["journalctl", "-u", name, "-n", str(lines), "--no-pager", "--output=short-iso"])
    return out if code == 0 else (err or out)


def do_systemctl(action, name):
    out, err, code = run_cmd(["systemctl", action, name])
    if code == 0:
        return True, out.strip() or f"{name} {action} 成功"
    else:
        hint = ""
        if "permission" in err.lower() or "not permitted" in err.lower():
            hint = "\n提示：可能需要以 sudo 或 pkexec 权限运行。"
        return False, (err.strip() or out.strip() or f"{name} {action} 失败") + hint

# —— 自动换行容器 —— #


class WrappingFrame(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.bind("<Configure>", self._on_configure)
        self.widgets = []

    def add(self, widget):
        self.widgets.append(widget)
        widget.grid(in_=self, row=0, column=len(self.widgets))

    def _on_configure(self, event):
        if not self.widgets:
            return
        btn_width = self.widgets[0].winfo_reqwidth() + 12
        cols = max(1, event.width // btn_width)
        for i, w in enumerate(self.widgets):
            r, c = divmod(i, cols)
            w.grid_configure(row=r, column=c, padx=6, pady=6)

# —— 主应用 —— #


class ServiceManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ubuntu 服务管理")
        self.geometry("1200x800")

        # 系统默认字体放大
        default_font = tkfont.nametofont("TkDefaultFont")
        text_font = tkfont.nametofont("TkTextFont")
        fixed_font = tkfont.nametofont("TkFixedFont")
        default_font.configure(size=14)
        text_font.configure(size=14)
        fixed_font.configure(size=13)
        self.option_add("*Font", default_font)

        self.services = []
        self.filtered = []
        self.selected_service = None

        self.sort_reverse = {}
        self.columns = ("name", "load", "active", "sub", "desc")
        self.col_titles = {
            "name": "服务名",
            "load": "加载",
            "active": "活动",
            "sub": "子状态",
            "desc": "描述"
        }

        self.create_widgets()
        self.refresh_services_async()

    def create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        ttk.Label(toolbar, text="搜索：").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            toolbar, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=8)
        search_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        ttk.Button(toolbar, text="刷新列表", command=self.refresh_services_async).pack(
            side=tk.LEFT, padx=8)

        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # 左侧服务列表
        left = ttk.Frame(main)
        main.add(left, weight=1)
        self.tree = ttk.Treeview(
            left, columns=self.columns, show="headings", height=20)
        for col in self.columns:
            self.tree.heading(col, text=self.col_titles[col],
                              command=lambda c=col: self.sort_by(c))
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_service)

        # 右侧详情与操作
        right = ttk.Frame(main)
        main.add(right, weight=2)

        actions = ttk.LabelFrame(right, text="服务操作")
        actions.pack(fill=tk.X, padx=4, pady=4)

        wrap = WrappingFrame(actions)
        wrap.pack(fill=tk.X)

        # 操作按钮
        for text, action in [("启动", "start"), ("停止", "stop"),
                             ("重启", "restart"), ("启用", "enable"), ("禁用", "disable")]:
            btn = ttk.Button(
                wrap, text=text, command=lambda a=action: self.do_action_async(a))
            wrap.add(btn)

        # 更新按钮
        btn_update = ttk.Button(
            wrap, text="更新", command=self.update_service_file)
        wrap.add(btn_update)

        btn_delete = ttk.Button(wrap, text="删除", command=self.delete_service_file)
        wrap.add(btn_delete)


        detail = ttk.Panedwindow(right, orient=tk.VERTICAL)
        detail.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        status_frame = ttk.LabelFrame(detail, text="服务状态")
        logs_frame = ttk.LabelFrame(detail, text="最近日志")
        detail.add(status_frame, weight=1)
        detail.add(logs_frame, weight=1)

        self.status_text = tk.Text(
            status_frame, wrap="none", height=12, font=("Monospace", 13))
        self.status_text.pack(fill=tk.BOTH, expand=True)

        self.logs_text = tk.Text(
            logs_frame, wrap="none", height=12, font=("Monospace", 13))
        self.logs_text.pack(fill=tk.BOTH, expand=True)

        self.info_var = tk.StringVar(
            value="提示：部分操作需要管理员权限，建议以 sudo 或 pkexec 运行。")
        ttk.Label(self, textvariable=self.info_var, foreground="#555").pack(
            side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)

    # —— 排序 —— #
    def sort_by(self, col):
        col_index = {"name": 0, "load": 1,
                     "active": 2, "sub": 3, "desc": 4}[col]
        reverse = self.sort_reverse.get(col, False)
        self.filtered.sort(key=lambda x: x[col_index], reverse=reverse)
        self.sort_reverse[col] = not reverse
        for c in self.columns:
            title = self.col_titles[c]
            if c == col:
                arrow = "▼" if reverse else "▲"
                self.tree.heading(c, text=f"{title} {arrow}",
                                  command=lambda cc=c: self.sort_by(cc))
            else:
                self.tree.heading(c, text=title,
                                  command=lambda cc=c: self.sort_by(cc))
        self._reload_tree()

    # —— 列表刷新 —— #
    def refresh_services_async(self):
        self.info_var.set("正在刷新服务列表…")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        services, err = list_services()

        def update_ui():
            if err:
                messagebox.showerror("错误", f"获取服务列表失败：\n{err}")
                self.info_var.set("获取服务列表失败")
                return
            self.services = services
            self.apply_filter()
            self.info_var.set(f"已加载 {len(self.filtered)} 个服务")
        self.after(0, update_ui)

    def apply_filter(self):
        keyword = self.search_var.get().strip().lower()
        if keyword:
            self.filtered = [
                s for s in self.services if keyword in s[0].lower() or keyword in s[4].lower()]
        else:
            self.filtered = list(self.services)
        self._reload_tree()

    def _reload_tree(self):
        self.tree.delete(*self.tree.get_children())
        for s in self.filtered:
            self.tree.insert("", tk.END, values=s)

    # —— 服务详情 —— #
    def on_select_service(self, event=None):
        item = self.tree.selection()
        if not item:
            self.selected_service = None
            return
        values = self.tree.item(item[0], "values")
        self.selected_service = values[0]
        self.load_service_detail_async()

    def load_service_detail_async(self):
        name = self.selected_service
        if not name:
            return
        self.info_var.set(f"加载 {name} 详情…")
        threading.Thread(target=self._detail_worker,
                         args=(name,), daemon=True).start()

    def _detail_worker(self, name):
        status = service_status(name)
        logs = journal_logs(name, lines=80)

        def update_ui():
            self._set_text(self.status_text, status)
            self._set_text(self.logs_text, logs)
            self.info_var.set(f"已加载 {name} 状态与日志")
        self.after(0, update_ui)

    def _set_text(self, widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state="normal")

    # —— 服务操作 —— #
    def do_action_async(self, action):
        name = self.selected_service
        if not name:
            messagebox.showinfo("提示", "请先选择一个服务。")
            return
        self.info_var.set(f"执行 {name} 的 {action}…")
        threading.Thread(target=self._action_worker, args=(
            action, name), daemon=True).start()

    def _action_worker(self, action, name):
        ok, msg = do_systemctl(action, name)

        def update_ui():
            if ok:
                self.info_var.set(msg)
                self.load_service_detail_async()
                self.refresh_services_async()
            else:
                self.info_var.set("操作失败")
                messagebox.showerror("操作失败", msg)
        self.after(0, update_ui)

    def update_service_file(self):
        name = self.selected_service

        filepath = filedialog.askopenfilename(
            title="选择 service 文件",
            filetypes=[("Service files", "*.service"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            if name:  # 已选中服务 → 更新
                target = os.path.join("/etc/systemd/system", name)
                if not messagebox.askyesno("确认更新", f"确定要用 {filepath} 覆盖 {target} 并重启服务吗？"):
                    return
                shutil.copy(filepath, target)
                run_cmd(["systemctl", "daemon-reload"])
                ok, msg = do_systemctl("restart", name)
                if ok:
                    messagebox.showinfo("成功", f"{name} 已更新并重启成功")
                    self.info_var.set(f"{name} 已更新并重启成功")
                    self.load_service_detail_async()
                else:
                    messagebox.showerror("失败", msg)
                    self.info_var.set("更新失败")

            else:  # 未选中服务 → 添加新服务
                # 询问服务名
                new_name = simpledialog.askstring("添加服务", "请输入新服务文件名（例如 myapp.service）：")
                if not new_name or not new_name.endswith(".service"):
                    messagebox.showwarning("无效输入", "必须输入以 .service 结尾的文件名。")
                    return

                target = os.path.join("/etc/systemd/system", new_name)
                if os.path.exists(target):
                    if not messagebox.askyesno("覆盖确认", f"{new_name} 已存在，是否覆盖？"):
                        return

                shutil.copy(filepath, target)
                run_cmd(["systemctl", "daemon-reload"])
                do_systemctl("enable", new_name)
                ok, msg = do_systemctl("start", new_name)

                if ok:
                    messagebox.showinfo("成功", f"{new_name} 已添加并启动成功")
                    self.info_var.set(f"{new_name} 已添加并启动成功")
                    self.refresh_services_async()
                else:
                    messagebox.showerror("失败", msg)
                    self.info_var.set("添加失败")

        except PermissionError:
            messagebox.showerror("权限错误", "需要管理员权限才能操作。\n请用 sudo 或 pkexec 运行本程序。")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败：{e}")


    def delete_service_file(self):
        name = self.selected_service
        if not name:
            messagebox.showinfo("提示", "请先选择一个服务。")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除服务 {name} 吗？\n这将停止并移除该服务。"):
            return

        try:
            # 停止并禁用
            do_systemctl("disable", name)
            do_systemctl("stop", name)

            # 删除 service 文件
            target = os.path.join("/etc/systemd/system", name)
            if os.path.exists(target):
                os.remove(target)

            # 重新加载 systemd
            run_cmd(["systemctl", "daemon-reload"])

            messagebox.showinfo("成功", f"{name} 已删除")
            self.info_var.set(f"{name} 已删除")
            self.refresh_services_async()

        except PermissionError:
            messagebox.showerror("权限错误", "需要管理员权限才能删除服务。\n请用 sudo 或 pkexec 运行本程序。")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{e}")



def main():
    app = ServiceManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
