import os
import random
import time
import requests
from fake_useragent import UserAgent
import csv
import concurrent.futures

# ==============================
# CONFIGURACIÓN
# ==============================
SESSION_ID = "48884460708%3AXDbufgBaTNWnRA%3A23%3AAYiIf9CsG6xce_pdI6GATYjneZWEo0KnEfHdwIcbVA"


# ==============================
# OBTENER DETALLES DE UN USUARIO
# ==============================
def get_user_details(username, session_id):
    headers = {
        "user-agent": UserAgent().random,
        "x-ig-app-id": "936619743392459",
        "x-requested-with": "XMLHttpRequest",
        "referer": f"https://www.instagram.com/{username}/"
    }

    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

    try:
        r = requests.get(
            url,
            headers=headers,
            cookies={"sessionid": session_id},
            timeout=10
        )

        if r.status_code == 200:
            user = r.json()["data"]["user"]
            return {
                "username": user["username"],
                "follower_count": user["edge_followed_by"]["count"],
                "following_count": user["edge_follow"]["count"],
                "biography": user.get("biography", ""),
                "category": user.get("category_name", "")
            }

    except Exception as e:
        print(f"Error obteniendo {username}: {e}")

    return None


# ==============================
# OBTENER LISTA DE SEGUIDOS
# ==============================
def get_following_list(target_username, session_id):
    headers = {
        "user-agent": UserAgent().random,
        "x-ig-app-id": "936619743392459",
        "x-requested-with": "XMLHttpRequest",
        "referer": f"https://www.instagram.com/{target_username}/"
    }

    url_info = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={target_username}"

    r = requests.get(
        url_info,
        headers=headers,
        cookies={"sessionid": session_id}
    )

    if r.status_code != 200:
        print("No se pudo obtener el usuario objetivo")
        return []

    user_id = r.json()["data"]["user"]["id"]

    following = []
    max_id = None

    print("\nObteniendo seguidos...\n")

    while True:
        params = {"count": "50"}
        if max_id:
            params["max_id"] = max_id

        url = f"https://www.instagram.com/api/v1/friendships/{user_id}/following/"

        r = requests.get(
            url,
            headers=headers,
            cookies={"sessionid": session_id},
            params=params,
            timeout=30
        )

        if r.status_code != 200:
            break

        data = r.json()
        users = data.get("users", [])

        if not users:
            break

        for u in users:
            following.append(u["username"])

        if not data.get("next_max_id"):
            break

        max_id = data["next_max_id"]
        time.sleep(random.uniform(1, 2))

    print(f"Seguidos obtenidos: {len(following)}")
    return following


# ==============================
# PROCESAR SEGUIDOS EN PARALELO
# ==============================
def scrape_following_details(target_username, session_id, threads):
    following_list = get_following_list(target_username, session_id)

    chunks = [following_list[i::threads] for i in range(threads)]
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(
                lambda batch: [
                    get_user_details(u, session_id) for u in batch
                ],
                chunk
            )
            for chunk in chunks
        ]

        for f in concurrent.futures.as_completed(futures):
            for item in f.result():
                if item:
                    results.append(item)

    return results


# ==============================
# GUARDAR CSV
# ==============================
def save_csv(data, filename):
    os.makedirs("PROFILES_DATA", exist_ok=True)
    path = os.path.join("PROFILES_DATA", filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "username",
                "follower_count",
                "following_count",
                "biography",
                "category"
            ]
        )
        writer.writeheader()
        writer.writerows(data)

    print(f"\nCSV guardado en: {path}")


# ==============================
# MAIN
# ==============================
def main():
    target_username = input("Username objetivo: ").strip()
    threads = int(input("Número de hilos: "))

    data = scrape_following_details(
        target_username, SESSION_ID, threads
    )

    print(f"\nSeguidos procesados: {len(data)}")
    save_csv(data, f"{target_username}_following_details.csv")


if __name__ == "__main__":
    main()
