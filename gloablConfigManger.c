#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <sys/stat.h>


#define GREEN   "\033[1;32m"
#define RED     "\033[1;31m"
#define BLUE    "\033[1;34m"
#define CYAN    "\033[1;36m"
#define YELLOW  "\033[1;33m"
#define RESET   "\033[0m"
#define LINE    "=================================================="

/* 路径配置定义 */
#define ARCHOS_ROOT     "./archos/airootfs"
#define WAYLAND_PATH    ARCHOS_ROOT "/usr/share/archos-wayland/configs"
#define WAYLAND_SCRIPT  ARCHOS_ROOT "/usr/share/archos-wayland/import-wayland.sh"
#define PACKAGE_CONFIG  "./archos/packages.x86_64"
#define LOCALE_CONFIG   ARCHOS_ROOT "/etc/locale.conf"
#define VCONSOLE_CONFIG ARCHOS_ROOT "/etc/vconsole.conf"

/* UI 提示函数 */
void header(const char *title) 
{
    printf("\n");
    printf(CYAN LINE RESET "\n");
    printf(CYAN "        BaoLinux Global Manager\n" RESET);
    printf(CYAN "        %s\n" RESET, title);
    printf(CYAN LINE RESET "\n");
}

void status_ok(const char *msg) 
{
    printf(GREEN "[✓] %s\n" RESET, msg);
}

void status_error(const char *msg) 
{
    printf(RED "[✗] %s\n" RESET, msg);
}

void edit_file(const char *path) 
{
    char cmd[512];

    printf(YELLOW "[EDIT] " RESET "%s\n", path);
    snprintf(cmd, sizeof(cmd), "nano '%s'", path);
    system(cmd);

    status_ok("Configuration updated");
}

/* ==================== 1. 软件包配置 ==================== */
void setUpPackageConfig() 
{
    header("Package Configuration");
    printf(BLUE "File:\n" RESET "%s\n\n", PACKAGE_CONFIG);
    edit_file(PACKAGE_CONFIG);
}

void show_wayland() 
{
    DIR *dir;
    struct dirent *entry;

    header("Installed Wayland");

    dir = opendir(WAYLAND_PATH);
    if (!dir) {
        status_error("No Wayland config found");
        return;
    }

    printf(BLUE "Available DE:\n\n" RESET);
    while ((entry = readdir(dir))) {
     
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }

        char full_path[512];
        struct stat st;
        snprintf(full_path, sizeof(full_path), "%s/%s", WAYLAND_PATH, entry->d_name);

        if (stat(full_path, &st) == 0 && S_ISDIR(st.st_mode)) {
            printf(CYAN "  - %s\n" RESET, entry->d_name);
        }
    }
    closedir(dir);
}

void delete_wayland() 
{
    char name[128];
    char path[512];
    char confirm[8];

    show_wayland();

    printf(YELLOW "\nDelete DE> " RESET);
    fgets(name, sizeof(name), stdin);
    name[strcspn(name, "\n")] = 0;

    snprintf(path, sizeof(path), "%s/%s", WAYLAND_PATH, name);

    if (access(path, F_OK) != 0) {
        status_error("DE not found");
        return;
    }

    printf(RED "Delete %s ? (y/N): " RESET, name);
    fgets(confirm, sizeof(confirm), stdin);

    if (confirm[0] == 'y' || confirm[0] == 'Y') {
        char cmd[1024]; 
        snprintf(cmd, sizeof(cmd), "rm -rf '%s'", path);
        system(cmd);
        status_ok("Wayland config removed");
    } else {
        printf("Cancelled\n");
    }
}

void setUpWaylandConfig() 
{
    char choice[16];

    while (1) {
        header("Wayland Manager");
        printf(
            CYAN "1" RESET ". Show installed Wayland\n"
            CYAN "2" RESET ". Edit import-wayland.sh\n"
            CYAN "3" RESET ". Delete Wayland config\n"
            CYAN "4" RESET ". Back\n\n"
        );

        printf(YELLOW "Choose > " RESET);
        fgets(choice, sizeof(choice), stdin);

        switch (atoi(choice)) {
            case 1:
                show_wayland();
                break;
            case 2:
                edit_file(WAYLAND_SCRIPT);
                break;
            case 3:
                delete_wayland();
                break;
            case 4:
                return;
            default:
                status_error("Invalid option");
        }
    }
}

/* ==================== 3. 语言与键盘本地化 ==================== */
void setUpLanguageConfig() 
{
    header("Language Configuration");
    edit_file(LOCALE_CONFIG);
    edit_file(VCONSOLE_CONFIG);
}

/* ==================== 主菜单与控制流 ==================== */
void buildISO() 
{
    header("Build ISO");
    printf(YELLOW "Building ISO...\n" RESET);
    system("sudo mkarchiso -v archos");
    status_ok("ISO build completed");
}


int menu_loop() 
{
    char choice[16];

    while (1) {
        header("System Configuration");
        printf(
            CYAN "1" RESET ". Package config\n"
            CYAN "2" RESET ". Wayland config\n"
            CYAN "3" RESET ". Language config\n"
            CYAN "4" RESET ". BuildISO\n"
            CYAN "5" RESET ". Exit\n"
        );

        printf(YELLOW "Choose > " RESET);
        fgets(choice, sizeof(choice), stdin);

        switch (atoi(choice)) {
            case 1:
                setUpPackageConfig();
                break;
            case 2:
                setUpWaylandConfig();
                break;
            case 3:
                setUpLanguageConfig();
                break;
            case 4:
                buildISO();
                break;
            case 5:
                printf(GREEN "\nBye!\n" RESET);
                return 0;
            default:
                status_error("Invalid selection");
        }
    }
}

int main() 
{

    if (access(ARCHOS_ROOT, F_OK) != 0) {
        status_error("archos/airootfs not found");
        return 1;
    }

    return menu_loop();
}