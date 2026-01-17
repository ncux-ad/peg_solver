# Установка системных зависимостей

Для компиляции Cython расширений нужны системные пакеты разработки.

## Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y python3-dev build-essential
```

## Fedora/RHEL/CentOS

```bash
sudo dnf install -y python3-devel gcc gcc-c++ make
```

## Arch Linux

```bash
sudo pacman -S --noconfirm python base-devel
```

## Проверка установки

После установки проверьте:

```bash
python3 -c "import sysconfig; print(sysconfig.get_path('include'))"
ls $(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")/Python.h
```

Если файл найден - всё готово!

## Быстрая установка для Ubuntu/Debian

```bash
sudo apt-get update && sudo apt-get install -y python3-dev build-essential
```
