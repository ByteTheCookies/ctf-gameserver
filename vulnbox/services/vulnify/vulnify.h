#ifndef VULNIFY_H
#define VULNIFY_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>
#include <locale.h>

#define USERNAME_LENGTH 32
#define PASSWORD_LENGTH 32
#define PLAYLIST_NAME_LENGTH 32
#define PLAYLIST_DESCRIPTION_LENGTH 128
#define SONG_NAME_LENGTH 32
#define MAX_SONGS 24

#define USER_LINE_LENGTH (USERNAME_LENGTH + PASSWORD_LENGTH + 5)
#define PLAYLIST_LINE_LENGTH (PLAYLIST_NAME_LENGTH + PLAYLIST_DESCRIPTION_LENGTH + (SONG_NAME_LENGTH + 1) * MAX_SONGS + 3)
#define USER_PATH_LENGTH USERNAME_LENGTH + 6
#define PLAYLIST_PATH_LENGTH USER_PATH_LENGTH + PLAYLIST_NAME_LENGTH + 1

typedef struct playlist_t playlist;
typedef struct user_t user;

void generate_password(char*, char*);

void main_menu();
void user_menu();

uint8_t register_user();
uint8_t login();

void create_playlist();
void inspect_playlists();
void play_random_song();


#endif
