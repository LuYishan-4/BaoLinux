#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/crypto.h>

#define KEY_SIZE 32
#define IV_SIZE 16
#define MAX_STR 256

typedef struct {
    char resolution[MAX_STR];
    char kernel_params[MAX_STR];
    char timeout[10];
    char theme_name[MAX_STR];
    char encrypted_root_password[MAX_STR];
} GrubConfig;

const char *TARGET_DIR  = "archos";
const char *KEY_FILE    = "archos/grub_secret.key";
const char *CONFIG_FILE = "archos/grub_config.enc";
const char *PYTHON_HELPER = "sync_all_configs.py";

void safe_strcpy(char *dest, const char *src, size_t dest_size) {
    if (dest_size == 0) return;
    if (src == NULL) {
        dest[0] = '\0';
        return;
    }
    snprintf(dest, dest_size, "%s", src);
}

void enforce_permissions(const char *filename) {
    chmod(filename, S_IRUSR | S_IWUSR);
}

void print_config_summary(const GrubConfig *config) {
    printf("\n=== BaoLinux Global Config ===\n");
    printf("Resolution     : %s\n", config->resolution);
    printf("Kernel Params  : %s\n", config->kernel_params);
    printf("Timeout        : %s seconds\n", config->timeout);
    printf("Theme Name     : %s\n", config->theme_name);
    printf("Root Password  : %s\n", config->encrypted_root_password[0] ? "<set>" : "<empty>");
}

void json_escape(const char *input, char *out, size_t out_size) {
    size_t j = 0;
    for (size_t i = 0; input[i] != '\0' && j + 1 < out_size; ++i) {
        switch (input[i]) {
            case '\\':
                if (j + 2 < out_size) {
                    out[j++] = '\\';
                    out[j++] = '\\';
                }
                break;
            case '"':
                if (j + 2 < out_size) {
                    out[j++] = '\\';
                    out[j++] = '"';
                }
                break;
            case '\n':
                if (j + 2 < out_size) {
                    out[j++] = '\\';
                    out[j++] = 'n';
                }
                break;
            default:
                out[j++] = input[i];
                break;
        }
    }
    out[j] = '\0';
}

int load_or_generate_crypto_keys(unsigned char *key, unsigned char *iv) {
    FILE *kf = fopen(KEY_FILE, "rb");
    if (kf) {
        size_t rk = fread(key, 1, KEY_SIZE, kf);
        size_t ri = fread(iv, 1, IV_SIZE, kf);
        fclose(kf);
        if (rk == KEY_SIZE && ri == IV_SIZE) return 0;
    }

    if (!RAND_bytes(key, KEY_SIZE) || !RAND_bytes(iv, IV_SIZE)) return -1;

    kf = fopen(KEY_FILE, "wb");
    if (!kf) return -1;
    fwrite(key, 1, KEY_SIZE, kf);
    fwrite(iv, 1, IV_SIZE, kf);
    fclose(kf);
    enforce_permissions(KEY_FILE);
    return 0;
}

int encrypt_config(GrubConfig *config, const unsigned char *key, const unsigned char *iv) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;

    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    int input_len = sizeof(GrubConfig);
    unsigned char *ciphertext = malloc(input_len + EVP_MAX_BLOCK_LENGTH);
    if (!ciphertext) { EVP_CIPHER_CTX_free(ctx); return -1; }

    int len = 0, ciphertext_len = 0;
    EVP_EncryptUpdate(ctx, ciphertext, &len, (unsigned char *)config, input_len);
    ciphertext_len = len;
    EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
    ciphertext_len += len;
    EVP_CIPHER_CTX_free(ctx);

    FILE *cf = fopen(CONFIG_FILE, "wb");
    if (!cf) { free(ciphertext); return -1; }
    fwrite(ciphertext, 1, ciphertext_len, cf);
    fclose(cf);
    enforce_permissions(CONFIG_FILE);
    free(ciphertext);

    OPENSSL_cleanse(config, sizeof(GrubConfig));
    return 0;
}

int decrypt_config(GrubConfig *config, const unsigned char *key, const unsigned char *iv) {
    FILE *cf = fopen(CONFIG_FILE, "rb");
    if (!cf) return -1;

    fseek(cf, 0, SEEK_END);
    long file_size = ftell(cf);
    fseek(cf, 0, SEEK_SET);
    if (file_size <= 0) { fclose(cf); return -1; }

    unsigned char *ciphertext = malloc(file_size);
    if (!ciphertext) { fclose(cf); return -1; }
    size_t rb = fread(ciphertext, 1, file_size, cf);
    fclose(cf);
    if ((long)rb != file_size) { free(ciphertext); return -1; }

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { free(ciphertext); return -1; }

    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) {
        EVP_CIPHER_CTX_free(ctx); free(ciphertext); return -1;
    }

    int len = 0;
    unsigned char *plaintext = malloc(file_size + EVP_MAX_BLOCK_LENGTH);
    if (!plaintext) { EVP_CIPHER_CTX_free(ctx); free(ciphertext); return -1; }

    if (EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext, file_size) != 1) {
        EVP_CIPHER_CTX_free(ctx); free(ciphertext); free(plaintext); return -1;
    }
    if (EVP_DecryptFinal_ex(ctx, plaintext + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx); free(ciphertext); free(plaintext); return -1;
    }
    memcpy(config, plaintext, sizeof(GrubConfig));
    EVP_CIPHER_CTX_free(ctx);
    free(ciphertext);
    OPENSSL_cleanse(plaintext, file_size + EVP_MAX_BLOCK_LENGTH);
    free(plaintext);
    return 0;
}

void auto_detect_host_info(GrubConfig *config) {
    safe_strcpy(config->resolution, "1920x1080", sizeof(config->resolution));
    safe_strcpy(config->kernel_params, "quiet splash", sizeof(config->kernel_params));
    safe_strcpy(config->timeout, "5", sizeof(config->timeout));
    safe_strcpy(config->theme_name, "BaoLinux-Theme", sizeof(config->theme_name));
    safe_strcpy(config->encrypted_root_password, "", sizeof(config->encrypted_root_password));

    FILE *fp = popen("/usr/bin/xrandr 2>/dev/null | /usr/bin/grep ' primary' | /usr/bin/awk '{print $4}' | /usr/bin/cut -d'+' -f1", "r");
    if (fp) {
        char buffer[MAX_STR];
        if (fgets(buffer, sizeof(buffer), fp) != NULL) {
            buffer[strcspn(buffer, "\n")] = 0;
            if (strchr(buffer, 'x')) safe_strcpy(config->resolution, buffer, sizeof(config->resolution));
        }
        pclose(fp);
    }
}

int prompt_value(const char *label, const char *current, char *out, size_t out_size) {
    char input[MAX_STR];
    printf("%s [%s]: ", label, current && current[0] ? current : "(empty)");
    if (!fgets(input, sizeof(input), stdin)) return -1;
    input[strcspn(input, "\n")] = 0;
    if (input[0] == '\0') {
        if (current) safe_strcpy(out, current, out_size);
        else out[0] = '\0';
        return 0;
    }
    safe_strcpy(out, input, out_size);
    return 1;
}

int interactive_setup(const unsigned char *key, const unsigned char *iv) {
    GrubConfig config;
    auto_detect_host_info(&config);

    printf("\n=== BaoLinux Global Config Setup ===\n");
    if (prompt_value("1. Target Resolution", config.resolution, config.resolution, sizeof(config.resolution)) < 0) return -1;
    if (prompt_value("2. Kernel Parameters", config.kernel_params, config.kernel_params, sizeof(config.kernel_params)) < 0) return -1;
    if (prompt_value("3. Menu Timeout", config.timeout, config.timeout, sizeof(config.timeout)) < 0) return -1;
    if (prompt_value("4. Theme Name", config.theme_name, config.theme_name, sizeof(config.theme_name)) < 0) return -1;
    if (prompt_value("5. Root Password (optional)", config.encrypted_root_password, config.encrypted_root_password, sizeof(config.encrypted_root_password)) < 0) return -1;

    print_config_summary(&config);
    if (encrypt_config(&config, key, iv) != 0) {
        fprintf(stderr, "[-] Failed to save encrypted config.\n");
        return -1;
    }

    printf("[+] Encrypted config saved to %s\n", CONFIG_FILE);
    return 0;
}

int show_config_from_disk(const unsigned char *key, const unsigned char *iv) {
    GrubConfig active_config;
    if (decrypt_config(&active_config, key, iv) != 0) {
        fprintf(stderr, "[-] No decrypted config available. Run setup first.\n");
        return -1;
    }
    print_config_summary(&active_config);
    OPENSSL_cleanse(&active_config, sizeof(GrubConfig));
    return 0;
}

int apply_config_to_python(const unsigned char *key, const unsigned char *iv) {
    GrubConfig active_config;
    if (decrypt_config(&active_config, key, iv) != 0) {
        fprintf(stderr, "[-] No decrypted config available. Run setup first.\n");
        return -1;
    }

    char escaped_resolution[MAX_STR * 2];
    char escaped_kernel[MAX_STR * 2];
    char escaped_theme[MAX_STR * 2];
    char escaped_password[MAX_STR * 2];
    json_escape(active_config.resolution, escaped_resolution, sizeof(escaped_resolution));
    json_escape(active_config.kernel_params, escaped_kernel, sizeof(escaped_kernel));
    json_escape(active_config.theme_name, escaped_theme, sizeof(escaped_theme));
    json_escape(active_config.encrypted_root_password, escaped_password, sizeof(escaped_password));

    char json_payload[4096];
    snprintf(json_payload, sizeof(json_payload),
             "{\"resolution\":\"%s\",\"kernel_params\":\"%s\",\"timeout\":\"%s\",\"theme_name\":\"%s\",\"root_password\":\"%s\"}",
             escaped_resolution, escaped_kernel, active_config.timeout, escaped_theme, escaped_password);

    printf("[+] Calling Python helper for synchronization...\n");
    char command[8192];
    snprintf(command, sizeof(command), "/usr/bin/python3 %s '%s'", PYTHON_HELPER, json_payload);
    int ret = system(command);
    if (ret == 0) {
        printf("[🎉] Synchronization pipeline completed successfully.\n");
    } else {
        fprintf(stderr, "[-] Error: Python helper returned an anomaly.\n");
    }

    OPENSSL_cleanse(&active_config, sizeof(GrubConfig));
    return ret == 0 ? 0 : -1;
}

int menu_loop(const unsigned char *key, const unsigned char *iv) {
    char choice[16];
    while (1) {
        printf("\n=== BaoLinux Global Manager ===\n");
        printf("1. Create / Update config\n");
        printf("2. Show current config\n");
        printf("3. Apply config to Python sync scripts\n");
        printf("4. Exit\n");
        printf("Choose: ");
        if (!fgets(choice, sizeof(choice), stdin)) break;

        int selected = atoi(choice);
        switch (selected) {
            case 1:
                interactive_setup(key, iv);
                break;
            case 2:
                show_config_from_disk(key, iv);
                break;
            case 3:
                apply_config_to_python(key, iv);
                break;
            case 4:
                return 0;
            default:
                printf("[-] Invalid selection.\n");
                break;
        }
    }
    return 0;
}

int main(int argc, char *argv[]) {
    unsigned char key[KEY_SIZE];
    unsigned char iv[IV_SIZE];

    struct stat st = {0};
    if (stat(TARGET_DIR, &st) == -1) mkdir(TARGET_DIR, 0755);

    if (load_or_generate_crypto_keys(key, iv) != 0) return 1;

    if (argc > 1 && strcmp(argv[1], "--json") == 0) {
        GrubConfig active_config;
        if (decrypt_config(&active_config, key, iv) == 0) {
            printf("{\n  \"resolution\": \"%s\",\n  \"kernel_params\": \"%s\",\n  \"timeout\": \"%s\",\n  \"theme_name\": \"%s\",\n  \"root_password\": \"%s\"\n}\n",
                   active_config.resolution, active_config.kernel_params, active_config.timeout, active_config.theme_name, active_config.encrypted_root_password);
            OPENSSL_cleanse(&active_config, sizeof(GrubConfig));
        }
        return 0;
    }

    if (argc > 1 && strcmp(argv[1], "--setup") == 0) {
        return interactive_setup(key, iv) == 0 ? 0 : 1;
    }

    if (argc > 1 && strcmp(argv[1], "--show") == 0) {
        return show_config_from_disk(key, iv) == 0 ? 0 : 1;
    }

    if (argc > 1 && strcmp(argv[1], "--apply") == 0) {
        return apply_config_to_python(key, iv) == 0 ? 0 : 1;
    }

    if (access(CONFIG_FILE, F_OK) != 0) {
        printf("[i] No config found yet. Starting setup.\n");
        return interactive_setup(key, iv) == 0 ? 0 : 1;
    }

    return menu_loop(key, iv);
}