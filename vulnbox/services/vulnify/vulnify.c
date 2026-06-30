#include "vulnify.h"
#include <errno.h>
#include <time.h>

struct artist_t
{
	char name[ARTIST_NAME_LENGTH];
	char description[ARTIST_DESCRIPTION_LENGTH];
	uint8_t description_len;
};

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

static uint8_t __user_exists(char* name, char* path);
static uint8_t __playlist_exists(user* usr, char* name, char* path);
static uint8_t __check_string(char* string);
static void __load_user(const char* path, user* usr);
static uint8_t __save_user(const char* path, user* usr);
static void __encrypt(const char* key, char* data, char* buffer, uint8_t len);
static void __decrypt(const char* key, char* data, char* buffer, uint8_t len);
static void __print_hex(const char* data, uint8_t n);

int main(void)
{// {{{
	setvbuf(stdin, NULL, _IONBF, 0);
	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);
	setlocale(LC_ALL, "");

	user logged_user;

	srand((unsigned)time(NULL));

	main_menu(&logged_user);

	return 0;
}// }}}

static uint8_t __user_exists(char* name, char* path)
{// {{{
	name[strcspn(name, "\n")] = '\0';

	int n = snprintf(path, USER_PATH_LENGTH, "./data/%s", name);
	if (n < 0 || n >= USER_PATH_LENGTH)
		return 0;

	return access(path, F_OK) == 0;
}// }}}

/* playlists now live in data/<user>/playlists/<name> */
static uint8_t __playlist_exists(user* usr, char* name, char* path)
{// {{{
	name[strcspn(name, "\n")] = '\0';

	int n = snprintf(path, PLAYLIST_PATH_LENGTH, "./data/%s/playlists/%s", usr->username, name);
	if (n < 0 || n >= PLAYLIST_PATH_LENGTH)
		return 0;

	return access(path, F_OK) == 0;
}// }}}

/* artists now live in data/<user>/artists/<name> */
static uint8_t __artist_exists(user* usr, char* name, char* path)
{// {{{
	name[strcspn(name, "\n")] = '\0';

	int n = snprintf(path, ARTIST_PATH_LENGTH, "./data/%s/artists/%s", usr->username, name);
	if (n < 0 || n >= ARTIST_PATH_LENGTH)
		return 0;

	return access(path, F_OK) == 0;
}// }}}

static void __load_user(const char* path, user* usr)
{// {{{
	char fullpath[USER_PATH_LENGTH + 6];
	snprintf(fullpath, sizeof(fullpath), "%s/info", path);

	FILE* f = fopen(fullpath, "rb");
	if (!f)
	{
		perror("fopen");
		return;
	}

	size_t r = fread(usr, sizeof(*usr), 1, f);
	if (r != 1)
	{
		fprintf(stderr, "[ERROR] Failed to read user info\n");
	}
	fclose(f);
}// }}}

static uint8_t __save_user(const char* path, user* usr)
{// {{{
	char fullpath[USER_PATH_LENGTH + 6];
	snprintf(fullpath, sizeof(fullpath), "%s/info", path);

	FILE* uf = fopen(fullpath, "wb");
	if (!uf)
	{
		perror("fopen");
		return 0;
	}

	size_t w = fwrite(usr, sizeof(*usr), 1, uf);
	if (w != 1)
	{
		fprintf(stderr, "[ERROR] Failed to write user info\n");
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
		if (!isalnum((unsigned char)*string) && 
				*string != '_' && *string != ' ' && *string != '=' && *string != '+' && *string != '/')
			break;
		++string;
	}

	return *string == '\0';
}// }}}

static void __encrypt(const char* key, char* data, char* buffer, uint8_t len)
{// {{{
	uint8_t otp = 0;
	while (*key != '\0')
		otp ^= *key++ >> 1;

	for (uint8_t i = 0; i < len; ++i)
		buffer[i] = ((const uint8_t*)data)[i] ^ otp;
}// }}}

static void __decrypt(const char* key, char* data, char* buffer, uint8_t len)
{// {{{
	uint8_t otp = 0;
	while (*key != '\0')
		otp ^= *key++ >> 1;

	for (uint8_t i = 0; i < len; ++i)
		buffer[i] = data[i] ^ otp;
}// }}}

static void __print_hex(const char* data, uint8_t n)
{// {{{
	for (uint8_t i = 0; i < n; ++i) printf("%02x", data[i]);
}// }}}

void main_menu(user* usr)
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
				register_user(usr);
				run = 1;
				break;
			case '2':
				if (!login(usr)) run = 1;
				break;
			case '0':
				return;
			default:
				run = 1;
				break;
		}
	} while (run == 1);

	user_menu(usr);
}// }}}

void user_menu(user* usr)
{// {{{
	uint8_t run = 0;

	do
	{
		puts("\nSelect an option");
		puts("1. Create a new playlist");
		puts("2. Inspect your playlists");
		puts("3. Play a random song");
		puts("4. Add an artist");
		puts("5. Check an artist");
		puts("0. Exit");
		putchar('>'); putchar(' ');

		int c = getchar();
		if (c == EOF) return;
		int d;
		while ((d = getchar()) != '\n' && d != EOF) {}

		switch ((char)c)
		{
			case '1':
				create_playlist(usr);
				run = 1;
				break;
			case '2':
				inspect_playlists(usr);
				run = 1;
				break;
			case '3':
				play_random_song();
				run = 1;
				break;
			case '4':
				create_artist(usr);
				run = 1;
				break;
			case '5':
				decrypt_artist(usr);
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

uint8_t register_user(user* usr)
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

		char pdir[USER_PATH_LENGTH + 11];
		char adir[USER_PATH_LENGTH + 9];

		/* data/<user>/playlists */
		snprintf(pdir, sizeof(pdir), "%s/playlists", path);
		if (mkdir(pdir, 0777) != 0 && errno != EEXIST)
		{
			perror("mkdir playlists");
			return 0;
		}

		/* data/<user>/artists */
		snprintf(adir, sizeof(adir), "%s/artists", path);
		if (mkdir(adir, 0777) != 0 && errno != EEXIST)
		{
			perror("mkdir artists");
			return 0;
		}

		break;
	}
	username[strcspn(username, "\n")] = '\0';

	puts("Insert password");
	putchar('>'); putchar(' ');

	while (fgets(password, sizeof(password), stdin) == NULL || !__check_string(password))
	{
		puts("[ERROR] Invalid password");
		continue;
	}

	memset(usr, 0, sizeof(*usr));

	strcpy(usr->username, username);
	strcpy(usr->password, password);
	usr->saved_playlists = 0;

	if (!__save_user(path, usr))
	{
		puts("[ERROR] Failed to save user");
		return 0;
	}

	puts("\nUser successfully registered");
	return 1;
}// }}}

uint8_t login(user* usr)
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
			return 0;
		}
		break;
	}
	username[strcspn(username, "\n")] = '\0';

	__load_user(path, usr);

	puts("Insert password");
	putchar('>'); putchar(' ');

	if (fgets(password, sizeof(password), stdin) == NULL ||
	    strncmp(usr->password, password, strlen(password) - 1) != 0)
	{
		puts("[ERROR] Invalid password");
		return 0;
	}

	puts("\nLogin successful");
	return 1;
}// }}}

void create_artist(user* usr)
{// {{{
	char name[ARTIST_NAME_LENGTH];
	char description[ARTIST_DESCRIPTION_LENGTH];
	char path[ARTIST_PATH_LENGTH];
	char key[16 + 1];

	while (1)
	{
		puts("\nInsert artist name");
		putchar('>'); putchar(' ');

		if (!fgets(name, sizeof(name), stdin) || strlen(name) < 2 || !__check_string(name))
		{
			puts("[ERROR] Invalid name");
			continue;
		}

		name[strcspn(name, "\n")] = '\0';

		if (__artist_exists(usr, name, path))
		{
			puts("[ERROR] Artist with that name already exists");
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
		puts("\nInsert encryption key");
		putchar('>'); putchar(' ');

		if (!fgets(key, sizeof(key), stdin) || !__check_string(key))
		{
			puts("[ERROR] Invalid key");
			continue;
		}
		break;
	}
	key[strcspn(key, "\n")] = '\0';

	artist ar;
	memset(&ar, 0, sizeof(ar));

	strcpy(ar.name, name);
	ar.description_len = (uint8_t)strlen(description);
	__encrypt(key, description, ar.description, ar.description_len);

	puts("Encrypted description (hex):");
	__print_hex(ar.description, ar.description_len);
	putchar('\n');

	FILE* arf = fopen(path, "wb");
	if (!arf)
	{
		perror("fopen artist");
		return;
	}
	if (fwrite(&ar, sizeof(ar), 1, arf) != 1)
	{
		fprintf(stderr, "[ERROR] Failed to write artist\n");
		fclose(arf);
		return;
	}

	fclose(arf);

	puts("Artist successfully created");
}// }}}

void decrypt_artist(user* usr)
{// {{{
	char name[ARTIST_NAME_LENGTH];
	char path[ARTIST_PATH_LENGTH];
	char key[16 + 1];

	while (1)
	{
		puts("\nInsert artist name");
		putchar('>'); putchar(' ');

		if (!fgets(name, sizeof(name), stdin) || strlen(name) < 2 || !__check_string(name))
		{
			puts("[ERROR] Invalid name");
			continue;
		}

		name[strcspn(name, "\n")] = '\0';

		if (!__artist_exists(usr, name, path))
		{
			puts("[ERROR] Artist not found");
			return;
		}
		break;
	}

	while (1)
	{
		puts("\nInsert encryption key");
		putchar('>'); putchar(' ');

		if (!fgets(key, sizeof(key), stdin) || !__check_string(key))
		{
			puts("[ERROR] Invalid key");
			continue;
		}
		break;
	}
	key[strcspn(key, "\n")] = '\0';

	artist ar;
	memset(&ar, 0, sizeof(ar));

	FILE* f = fopen(path, "rb");
	if (!f)
	{
		perror("fopen artist");
		return;
	}

	if (fread(&ar, sizeof(ar), 1, f) != 1)
	{
		fprintf(stderr, "[ERROR] Failed to read artist\n");
		fclose(f);
		return;
	}
	fclose(f);

	uint8_t n = ar.description_len;
	if (n > ARTIST_DESCRIPTION_LENGTH) n = ARTIST_DESCRIPTION_LENGTH;

	char out[ARTIST_DESCRIPTION_LENGTH];
	memset(out, 0, sizeof(out));
	__decrypt(key, ar.description, out, n);

	printf("\nArtist: %s\nPlaintext (hex):\n", ar.name);
	__print_hex(out, n);
	putchar('\n');
}// }}}

void create_playlist(user* usr)
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

		if (__playlist_exists(usr, name, path))
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

	playlist pl;
	memset(&pl, 0, sizeof(pl));

	strcpy(pl.name, name);
	strcpy(pl.description, description);
	pl.saved_songs = num_songs;

	for (i = 0; i < num_songs; ++i)
		strcpy(pl.songs[i], songs[i]);


	FILE* plf = fopen(path, "wb");
	if (!plf)
	{
		perror("fopen playlist");
		return;
	}
	if (fwrite(&pl, sizeof(pl), 1, plf) != 1)
	{
		fprintf(stderr, "[ERROR] Failed to write playlist\n");
		return;
	}

	usr->saved_playlists++;

	fclose(plf);

	puts("Playlist successfully created");
}// }}}

void inspect_playlists(user* usr)
{// {{{
	char path[USER_PATH_LENGTH + 10];
	snprintf(path, sizeof(path), "./data/%s/playlists", usr->username);

	DIR* dir = opendir(path);
	if (!dir)
	{
		perror("opendir");
		return;
	}

	struct dirent* entry;
	while ((entry = readdir(dir)) != NULL)
	{
		if (entry->d_name[0] == '.')
			continue;

		char fpath[PLAYLIST_PATH_LENGTH];
		snprintf(fpath, sizeof(fpath), "%s/%s", path, entry->d_name);

		playlist pl;
		memset(&pl, 0, sizeof(pl));

		FILE* f = fopen(fpath, "rb");
		if (!f)
		{
			perror("fopen");
			continue;
		}
		if (fread(&pl, sizeof(pl), 1, f) != 1)
		{
			fprintf(stderr, "[ERROR] Failed to read playlist file: %s\n", fpath);
			fclose(f);
			continue;
		}
		fclose(f);

		printf("\nPlaylist: %s\n\"%s\"\n", pl.name, pl.description);
		for (uint8_t i = 0; i < pl.saved_songs && i < MAX_SONGS; ++i)
			printf("\tSong %hhd: %s\n", i, pl.songs[i]);
	}

	closedir(dir);
}// }}}

void play_random_song()
{// {{{
	puts("");
	switch (rand() % 5)
	{
		case 0:
			puts("👟🦈👟 Tralalero Tralala 👟🦈👟");
			break;
		case 1:
			puts("🌵🐘🌵 Lirili Larila 🌵🐘🌵");
			break;
		case 2:
			puts("💣🐊💣 Bombardilo Crocodilo 💣🐊💣");
			break;
		case 3:
			puts("🍂🌳🍂 Brr Brr Patapim 🍂🌳🍂");
			break;
		case 4:
			puts("🐱🐟🐱 Trulimero Trulicina 🐱🐟🐱");
			break;
		default:
			break;
	}
}// }}}

// vulns:
// can login with password prefix
// password can be empty
// weak encryption
