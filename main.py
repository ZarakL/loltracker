# main.py
from riot_api import calculate_stats

def main():
    riot_id = input("Enter your Riot ID (e.g., TFBlade#122): ")

    try:
        stats = calculate_stats(riot_id, match_count=20)
        overall_winrate = stats["overall_winrate"]
        total_matches = stats["total_matches"]
        overall_kda = stats["overall_kda"]
        champion_stats_list = stats["champion_stats"]  # Already sorted by games desc

        print(f"Riot ID: {riot_id}")
        print(f"Total Games Analyzed: {total_matches}")
        print(f"Overall Win Rate: {overall_winrate:.2f}%")
        print(f"Overall KDA: {overall_kda:.2f}")

        print("\nTop 3 Champions:")
        top_3_champs = champion_stats_list[:3]  # slice first 3
        for champ_info in top_3_champs:
            champ = champ_info["champion"]
            winrate = champ_info["winrate"]
            w = champ_info["wins"]
            l = champ_info["losses"]
            kda = champ_info["kda"]
            # Example line format: "Jax 44% (4W 5L) 2.92 KDA"
            print(f"{champ} {winrate:.0f}% ({w}W {l}L) {kda:.2f} KDA")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
