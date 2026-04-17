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
#define ARTIST_NAME_LENGTH 32
#define ARTIST_DESCRIPTION_LENGTH 64

#define USER_LINE_LENGTH (USERNAME_LENGTH + PASSWORD_LENGTH + 5)
#define PLAYLIST_LINE_LENGTH (PLAYLIST_NAME_LENGTH + PLAYLIST_DESCRIPTION_LENGTH + (SONG_NAME_LENGTH + 1) * MAX_SONGS + 3)

/*
 * Paths:
 *   user dir:      data/<username>
 *   user info:     data/<username>/info
 *   playlists dir: data/<username>/playlists
 *   artists dir:   data/<username>/artists
 *   playlist file: data/<username>/playlists/<playlistname>
 *   artist file:   data/<username>/artists/<artistname>
 */

/* "./data/" + "<username>" + NUL */
#define USER_PATH_LENGTH (8 + USERNAME_LENGTH + 1)

/* USER_PATH + "/playlists/" + "<playlistname>" + NUL */
#define PLAYLIST_PATH_LENGTH (USER_PATH_LENGTH + 11 + PLAYLIST_NAME_LENGTH + 1)

/* USER_PATH + "/artists/" + "<artistname>" + NUL */
#define ARTIST_PATH_LENGTH (USER_PATH_LENGTH + 9 + ARTIST_NAME_LENGTH + 1)

typedef struct artist_t artist;
typedef struct playlist_t playlist;
typedef struct user_t user;

void main_menu(user* usr);
void user_menu(user* usr);

uint8_t register_user(user* usr);
uint8_t login(user* usr);

void create_artist(user* usr);
void decrypt_artist(user* usr);

void create_playlist(user* usr);
void inspect_playlists(user* usr);
void play_random_song(void);


#endif
