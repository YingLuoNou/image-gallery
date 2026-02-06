import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
from PIL import Image, ImageTk

# ===========================
# 核心逻辑类 (负责文件操作)
# ===========================
class GalleryLogic:
    def __init__(self, root_path):
        self.root = Path(root_path)

    def get_categories(self):
        """获取所有子文件夹作为分类"""
        if not self.root.exists():
            return []
        return [d.name for d in self.root.iterdir() if d.is_dir()]

    def create_category(self, name):
        """创建新分类"""
        path = self.root / name
        if not path.exists():
            path.mkdir(parents=True)
            return True
        return False

    def get_images(self, category):
        """获取分类下的所有webp图片，按数字排序"""
        cat_path = self.root / category
        if not cat_path.exists():
            return []
        files = list(cat_path.glob("*.webp"))
        files.sort(key=lambda f: int(f.stem) if f.stem.isdigit() else float('inf'))
        return files

    def add_image(self, category, source_path):
        """转换并添加图片"""
        cat_path = self.root / category
        files = self.get_images(category)
        
        # 计算新序号
        if files:
            last_num = int(files[-1].stem)
            new_index = last_num + 1
        else:
            new_index = 1
            
        target_path = cat_path / f"{new_index}.webp"
        
        try:
            with Image.open(source_path) as img:
                img.save(target_path, 'WEBP', lossless=True)
            return True, target_path.name
        except Exception as e:
            return False, str(e)

    def delete_image(self, category, filename):
        """删除图片并重排"""
        cat_path = self.root / category
        target_file = cat_path / filename
        
        if target_file.exists():
            os.remove(target_file)
            self._renumber_images(cat_path)
            return True
        return False

    def _renumber_images(self, category_path):
        """重排逻辑"""
        files = list(category_path.glob("*.webp"))
        # 必须按当前文件名数字排序
        files.sort(key=lambda f: int(f.stem) if f.stem.isdigit() else float('inf'))
        
        for i, file_path in enumerate(files, start=1):
            expected_name = f"{i}.webp"
            if file_path.name != expected_name:
                new_path = category_path / expected_name
                file_path.rename(new_path)

# ===========================
# 图形界面类 (GUI)
# ===========================
class GalleryGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("本地图床管理器 (Python版)")
        self.master.geometry("900x600")
        
        self.logic = None
        self.current_category = None
        self.current_image_path = None

        # --- 顶部：目录选择 ---
        top_frame = tk.Frame(master, pady=10)
        top_frame.pack(fill=tk.X)
        
        self.path_label = tk.Label(top_frame, text="未选择图床根目录", fg="gray")
        self.path_label.pack(side=tk.LEFT, padx=10)
        
        btn_select = tk.Button(top_frame, text="选择根目录文件夹", command=self.select_root_folder)
        btn_select.pack(side=tk.RIGHT, padx=10)

        # --- 主体区域 ---
        main_pane = tk.PanedWindow(master, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 1. 左侧：分类列表
        left_frame = tk.Frame(main_pane)
        tk.Label(left_frame, text="📂 分类列表 (文件夹)", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.cat_listbox = tk.Listbox(left_frame, width=20)
        self.cat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cat_listbox.bind("<<ListboxSelect>>", self.on_category_select)
        
        # 分类操作按钮
        cat_btn_frame = tk.Frame(left_frame)
        cat_btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(cat_btn_frame, text="+ 新建分类", command=self.add_category).pack(fill=tk.X)
        
        main_pane.add(left_frame, width=200)

        # 2. 中间：图片列表
        mid_frame = tk.Frame(main_pane)
        tk.Label(mid_frame, text="🖼️ 图片列表", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.img_listbox = tk.Listbox(mid_frame, width=20)
        self.img_listbox.pack(fill=tk.BOTH, expand=True)
        self.img_listbox.bind("<<ListboxSelect>>", self.on_image_select)
        
        main_pane.add(mid_frame, width=150)

        # 3. 右侧：预览与操作
        right_frame = tk.Frame(main_pane, bg="#f0f0f0", bd=2, relief=tk.SUNKEN)
        
        self.preview_label = tk.Label(right_frame, text="无预览", bg="#f0f0f0")
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=20)
        
        btn_frame = tk.Frame(right_frame, bg="#f0f0f0")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        self.btn_add = tk.Button(btn_frame, text="➕ 添加新图片 (自动转WebP)", command=self.action_add_image, state=tk.DISABLED, bg="#d9f7be")
        self.btn_add.pack(fill=tk.X, pady=5)
        
        self.btn_del = tk.Button(btn_frame, text="🗑️ 删除当前图片 (自动重排)", command=self.action_delete_image, state=tk.DISABLED, bg="#ffccc7")
        self.btn_del.pack(fill=tk.X, pady=5)

        main_pane.add(right_frame)

        # --- 底部：状态栏 ---
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        status_bar = tk.Label(master, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- 交互逻辑 ---

    def select_root_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.logic = GalleryLogic(path)
            self.path_label.config(text=f"根目录: {path}", fg="black")
            self.refresh_categories()
            self.status_var.set("图床加载成功")

    def refresh_categories(self):
        if not self.logic: return
        self.cat_listbox.delete(0, tk.END)
        cats = self.logic.get_categories()
        for c in cats:
            self.cat_listbox.insert(tk.END, c)

    def add_category(self):
        if not self.logic:
            messagebox.showwarning("提示", "请先选择根目录")
            return
        name = simpledialog.askstring("新建分类", "请输入分类文件夹名称 (英文):")
        if name:
            if self.logic.create_category(name):
                self.refresh_categories()
                self.status_var.set(f"分类 {name} 创建成功")
            else:
                messagebox.showerror("错误", "文件夹创建失败或已存在")

    def on_category_select(self, event):
        selection = self.cat_listbox.curselection()
        if not selection: return
        
        self.current_category = self.cat_listbox.get(selection[0])
        self.btn_add.config(state=tk.NORMAL) # 允许添加图片
        self.refresh_images()

    def refresh_images(self):
        self.img_listbox.delete(0, tk.END)
        self.preview_label.config(image='', text="无预览")
        self.btn_del.config(state=tk.DISABLED)
        
        files = self.logic.get_images(self.current_category)
        for f in files:
            self.img_listbox.insert(tk.END, f.name)
            
    def on_image_select(self, event):
        selection = self.img_listbox.curselection()
        if not selection: return
        
        filename = self.img_listbox.get(selection[0])
        self.current_image_path = self.logic.root / self.current_category / filename
        
        # 显示预览
        self.show_preview(self.current_image_path)
        self.btn_del.config(state=tk.NORMAL)

    def show_preview(self, path):
        try:
            pil_image = Image.open(path)
            # 缩放到合适大小用于预览
            pil_image.thumbnail((400, 400)) 
            tk_image = ImageTk.PhotoImage(pil_image)
            
            self.preview_label.config(image=tk_image, text="")
            self.preview_label.image = tk_image # 必须保持引用，否则会被垃圾回收
        except Exception:
            self.preview_label.config(text="无法预览图片")

    def action_add_image(self):
        if not self.current_category: return
        
        file_paths = filedialog.askopenfilenames(title="选择图片 (支持多选)", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp")])
        if not file_paths: return

        count = 0
        for src in file_paths:
            success, msg = self.logic.add_image(self.current_category, src)
            if success:
                count += 1
        
        self.refresh_images()
        self.status_var.set(f"成功添加 {count} 张图片")
        messagebox.showinfo("完成", f"已成功处理并添加 {count} 张图片！")

    def action_delete_image(self):
        selection = self.img_listbox.curselection()
        if not selection: return
        
        filename = self.img_listbox.get(selection[0])
        
        if messagebox.askyesno("确认删除", f"确定要删除 {filename} 吗？\n删除后后续文件将自动重命名。"):
            if self.logic.delete_image(self.current_category, filename):
                self.refresh_images()
                self.status_var.set(f"已删除 {filename} 并完成重排")
            else:
                messagebox.showerror("错误", "删除失败")

if __name__ == "__main__":
    root = tk.Tk()
    app = GalleryGUI(root)
    root.mainloop()