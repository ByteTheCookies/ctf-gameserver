#include "vulnify.h"
#include <errno.h>
#include <time.h>

struct playlist_t
{
	char name[PLAYLIST_NAME_LENGTH];
	char description[PLAYLIST_DESCRIPTION_LENGTH];
	char songs[MAX_SONGS][SONG_NAME_LENGTH];
	uint8_t saved_songs;
};

struct user_t
{
	char username[USERNAME_LENGTH];
	char password[PASSWORD_LENGTH];
	uint8_t saved_playlists;
};

static user* g_logged = NULL;

static uint8_t __user_exists(char* name, char* path);
static uint8_t __playlist_exists(char* name, char* path);
static uint8_t __check_string(char* string);
static void __load_user(const char* path);
static uint8_t __save_user(const char* path, const user* usr);

int main(void)
{// {{{
	setvbuf(stdin, NULL, _IONBF, 0);
	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);
	setlocale(LC_ALL, "");

	g_logged = malloc(sizeof(*g_logged));
	if (!g_logged)
	{
		perror("malloc");
		return 1;
	}
	memset(g_logged, 0, sizeof(*g_logged));

	srand((unsigned)time(NULL));

	main_menu();

	free(g_logged);
	g_logged = NULL;
	return 0;
}// }}}

static uint8_t __user_exists(char* name, char* path)
{// {{{
	name[strcspn(name, "\n")] = '\0';

	int n = snprintf(path, USER_PATH_LENGTH, "data/%s", name);
	if (n < 0 || n >= USER_PATH_LENGTH)
		return 0;

	return access(path, F_OK) == 0;
}// }}}

static uint8_t __playlist_exists(char* name, char* path)
{// {{{
	name[strcspn(name, "\n")] = '\0';

	int n = snprintf(path, PLAYLIST_PATH_LENGTH, "data/%s/%s", g_logged->username, name);
	if (n < 0 || n >= PLAYLIST_PATH_LENGTH)
		return 0;

	return access(path, F_OK) == 0;
}// }}}

static void __load_user(const char* path)
{// {{{
	char fullpath[USER_PATH_LENGTH + 6];
	int n = snprintf(fullpath, sizeof(fullpath), "%s/info", path);
	if (n < 0 || n >= (int)sizeof(fullpath))
	{
		fprintf(stderr, "[ERROR] user info path too long\n");
		return;
	}

	FILE* f = fopen(fullpath, "rb");
	if (!f)
	{
		perror("fopen");
		return;
	}

	size_t r = fread(g_logged, sizeof(*g_logged), 1, f);
	if (r != 1)
	{
		fprintf(stderr, "[ERROR] failed to read user info\n");
		memset(g_logged, 0, sizeof(*g_logged));
	}
	fclose(f);
}// }}}

static uint8_t __save_user(const char* path, const user* usr)
{// {{{
	char fullpath[USER_PATH_LENGTH + 6];
	int n = snprintf(fullpath, sizeof(fullpath), "%s/info", path);
	if (n < 0 || n >= (int)sizeof(fullpath))
	{
		fprintf(stderr, "[ERROR] user info path too long\n");
		return 0;
	}

	FILE* uf = fopen(fullpath, "wb");
	if (!uf)
	{
		perror("fopen");
		return 0;
	}

	size_t w = fwrite(usr, sizeof(*usr), 1, uf);
	if (w != 1)
	{
		fprintf(stderr, "[ERROR] failed to write user info\n");
		fclose(uf);
		return 0;
	}

	if (fclose(uf) != 0)
	{
		perror("fclose");
		return 0;
	}

	return 1;
}// }}}

static uint8_t __check_string(char* string)
{// {{{
	string[strcspn(string, "\n")] = '\0';

	while (*string != '\0')
	{
		if (!isalnum((unsigned char)*string) && *string != ' ' && *string != '=')
			break;
		++string;
	}

	return *string == '\0';
}// }}}

void generate_password(char* username, char* password)
{// {{{
	uint32_t val = 1, tmp;

	size_t len = strlen(username);
	size_t limit = ((size_t)(len / 4.0f)) * 4;

	for (size_t j = 0; j < limit; j += 4)
	{
		uint32_t b0 = (unsigned char)username[j];
		uint32_t b1 = (unsigned char)username[j + 1];
		uint32_t b2 = (unsigned char)username[j + 2];
		uint32_t b3 = (unsigned char)username[j + 3];

		tmp = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3;
		val = (0xDEADu * (val + tmp) + 0xBEEFu);
	}
	snprintf(password, PASSWORD_LENGTH, "%u", val);
}// }}}

void main_menu(void)
{// {{{
	puts("Vulnify (version: 2.0.1)\n");
	uint8_t run = 0;

	do
	{
		run = 0;

		puts("\nSelect an option");
		puts("1. Register");
		puts("2. Login");
		puts("0. Exit");
		putchar('>'); putchar(' ');

		int c = getchar();
		if (c == EOF) return;
		int d;
		while ((d = getchar()) != '\n' && d != EOF) {}

		putchar('\n');

		switch ((char)c)
		{
			case '1':
				if (!register_user()) run = 1;
				break;
			case '2':
				if (!login()) run = 1;
				break;
			case '0':
				return;
			default:
				run = 1;
				break;
		}
	} while (run == 1);

	user_menu();
}// }}}

void user_menu(void)
{// {{{
	uint8_t run = 0;

	do
	{
		puts("\nSelect an option");
		puts("1. Create a new playlist");
		puts("2. Inspect your playlists");
		puts("3. Play a random song");
		puts("0. Exit");
		putchar('>'); putchar(' ');

		int c = getchar();
		if (c == EOF) return;
		int d;
		while ((d = getchar()) != '\n' && d != EOF) {}

		switch ((char)c)
		{
			case '1':
				create_playlist();
				run = 1;
				break;
			case '2':
				inspect_playlists();
				run = 1;
				break;
			case '3':
				play_random_song();
				run = 1;
				break;
			case '0':
				run = 0;
				break;
			default:
				run = 1;
				break;
		}
	} while (run);
}// }}}

uint8_t register_user(void)
{// {{{
	char username[USERNAME_LENGTH];
	char password[PASSWORD_LENGTH];
	char path[USER_PATH_LENGTH];

	while (1)
	{
		puts("Insert username");
		putchar('>'); putchar(' ');

		if (fgets(username, sizeof(username), stdin) == NULL ||
		    strlen(username) < 2 ||
		    !__check_string(username))
		{
			puts("[ERROR] Invalid username");
			continue;
		}

		if (__user_exists(username, path))
		{
			puts("[ERROR] Username already exists");
			continue;
		}

		if (mkdir("data", 0777) != 0 && errno != EEXIST)
		{
			perror("mkdir data");
			return 0;
		}

		if (mkdir(path, 0777) != 0)
		{
			perror("mkdir userdir");
			return 0;
		}

		break;
	}
	username[strcspn(username, "\n")] = '\0';

	puts("Insert password [Empty to generate a safe password automatically]");
	putchar('>'); putchar(' ');

	if (fgets(password, sizeof(password), stdin) == NULL || !__check_string(password))
	{
		puts("[ERROR] Invalid password");
		return 0;
	}

	if (password[0] == '\0')
	{
		generate_password(username, password);
		printf("Your password is: %s\n", password);
	}

	user usr;
	memset(&usr, 0, sizeof(usr));

	strcpy(usr.username, username);
	strcpy(usr.password, password);
	usr.saved_playlists = 0;

	if (!__save_user(path, &usr))
	{
		puts("[ERROR] Failed to save user");
		return 0;
	}

	memcpy(g_logged, &usr, sizeof(*g_logged));

	puts("\nUser successfully registered");
	return 1;
}// }}}

uint8_t login(void)
{// {{{
	char username[USERNAME_LENGTH];
	char password[PASSWORD_LENGTH];
	char path[USER_PATH_LENGTH];

	while (1)
	{
		puts("Insert username");
		putchar('>'); putchar(' ');

		if (fgets(username, sizeof(username), stdin) == NULL || !__user_exists(username, path))
		{
			puts("[ERROR] Username not found\n");
			continue;
		}
		break;
	}
	username[strcspn(username, "\n")] = '\0';

	__load_user(path);

	puts("Insert password");
	putchar('>'); putchar(' ');

	if (fgets(password, sizeof(password), stdin) == NULL || strlen(password) < 2 ||
	    strncmp(g_logged->password, password, strlen(password) - 1) != 0)
	{
		puts("[ERROR] Invalid password");
		return 0;
	}

	puts("\nLogin successful");
	return 1;
}// }}}

void create_playlist(void)
{// {{{
	char name[PLAYLIST_NAME_LENGTH];
	char description[PLAYLIST_DESCRIPTION_LENGTH];
	char song[SONG_NAME_LENGTH];
	char songs[MAX_SONGS][SONG_NAME_LENGTH];
	char path[PLAYLIST_PATH_LENGTH];
	uint8_t num_songs;

	while (1)
	{
		puts("\nInsert playlist name");
		putchar('>'); putchar(' ');

		if (!fgets(name, sizeof(name), stdin) || strlen(name) < 2 || !__check_string(name))
		{
			puts("[ERROR] Invalid name");
			continue;
		}

		name[strcspn(name, "\n")] = '\0';

		if (__playlist_exists(name, path))
		{
			puts("[ERROR] Playlist with that name already exists");
			continue;
		}
		break;
	}

	while (1)
	{
		puts("\nInsert description");
		putchar('>'); putchar(' ');

		if (!fgets(description, sizeof(description), stdin) || !__check_string(description))
		{
			puts("[ERROR] Invalid description");
			continue;
		}
		break;
	}
	description[strcspn(description, "\n")] = '\0';

	while (1)
	{
		puts("\nHow many songs do you want to insert?");
		putchar('>'); putchar(' ');

		if (scanf("%hhu%*c", &num_songs) != 1)
		{
			puts("[ERROR] Invalid number");
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {}
			continue;
		}

		if (num_songs >= MAX_SONGS || num_songs == 0)
		{
			printf("[ERROR] Select a positive number smaller than %hhd\n", MAX_SONGS);
			continue;
		}
		break;
	}

	puts("\nInsert songs");
	uint8_t i = 0;
	while (i < num_songs)
	{
		printf("Song %hhd: ", i);

		if (!fgets(song, sizeof(song), stdin) || !__check_string(song))
		{
			puts("[ERROR] Invalid song name");
			continue;
		}
		song[strcspn(song, "\n")] = '\0';

		strcpy(songs[i++], song);
	}
	putchar('\n');

	playlist* pl = malloc(sizeof(*pl));
	if (!pl)
	{
		perror("malloc playlist");
		return;
	}
	memset(pl, 0, sizeof(*pl));

	strcpy(pl->name, name);
	strcpy(pl->description, description);
	pl->saved_songs = num_songs;

	for (i = 0; i < num_songs; ++i)
		strcpy(pl->songs[i], songs[i]);

	g_logged->saved_playlists++;

	FILE* plf = fopen(path, "wb");
	if (!plf)
	{
		perror("fopen playlist");
		free(pl);
		return;
	}
	if (fwrite(pl, sizeof(*pl), 1, plf) != 1)
	{
		fprintf(stderr, "[ERROR] failed to write playlist\n");
	}
	fclose(plf);

	free(pl);
	pl = NULL;

	puts("Playlist successfully created");
}// }}}

void inspect_playlists(void)
{// {{{
	char path[USER_PATH_LENGTH], fpath[PLAYLIST_PATH_LENGTH];
	int n = snprintf(path, sizeof(path), "data/%s", g_logged->username);
	if (n < 0 || n >= (int)sizeof(path))
	{
		fprintf(stderr, "[ERROR] path too long\n");
		return;
	}

	DIR* dir = opendir(path);
	if (!dir)
	{
		perror("opendir");
		return;
	}

	struct dirent* entry;
	while ((entry = readdir(dir)) != NULL)
	{
		if (!strncmp(entry->d_name, "info", 4) || entry->d_name[0] == '.')
			continue;

		playlist* pl = malloc(sizeof(*pl));
		if (!pl)
		{
			perror("malloc playlist");
			break;
		}

		n = snprintf(fpath, sizeof(fpath), "%s/%s", path, entry->d_name);
		if (n < 0 || n >= (int)sizeof(fpath))
		{
			free(pl);
			continue;
		}

		FILE* f = fopen(fpath, "rb");
		if (!f)
		{
			perror("fopen");
			free(pl);
			continue;
		}
		if (fread(pl, sizeof(*pl), 1, f) != 1)
		{
			fprintf(stderr, "[ERROR] failed to read playlist file: %s\n", fpath);
			fclose(f);
			free(pl);
			continue;
		}
		fclose(f);

		printf("\nPlaylist: %s\n\"%s\"\n", pl->name, pl->description);
		for (uint8_t i = 0; i < pl->saved_songs && i < MAX_SONGS; ++i)
			printf("\tSong %hhd: %s\n", i, pl->songs[i]);

		free(pl);
	}

	closedir(dir);
}// }}}

void play_random_song(void)
{// {{{
	putchar('\n');
	switch (rand() % 5)
	{
		case 0:
			puts("👟🦈👟 Tralalero Tralala 👟🦈👟");
			break;
		case 1:
			puts("🌵🐘🌵 Lirili Larila 🌵🐘🌵\n");
			break;
		case 2:
			puts("💣🐊💣 Bombardilo Crocodilo 💣🐊💣\n");
			break;
		case 3:
			puts("🍂🌳🍂 Brr Brr Patapim 🍂🌳🍂\n");
			break;
		case 4:
			puts("🐱🐟🐱 Trulimero Trulicina 🐱🐟🐱\n");
			break;
		default:
			break;
	}
}// }}}

// vulns:
// can login with password prefix
// weak password generator
