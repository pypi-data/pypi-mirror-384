import algorithms

def main():
    print("🔮 Welcome to AlgoScope CLI")
    print("==========================\n")

    while True:
        print("📁 Choose an option:")
        print("1️⃣  Show all categories")
        print("2️⃣  Show algorithms in a category")
        print("3️⃣  Show specific algorithm code")
        print("4️⃣  Exit")
        choice = input("\n👉 Enter your choice (1-4): ").strip()

        if choice == "1":
            print("\n📂 Categories:\n")
            print(algorithms.show("category"))

        elif choice == "2":
            category_name = input("\n📚 Enter category name: ").strip()
            print(f"\n📚 Algorithms under '{category_name}':\n")
            print(algorithms.show(category_name))

        elif choice == "3":
            algo_name = input("\n🔍 Enter algorithm name: ").strip()
            print(f"\n📜 Code for '{algo_name}':\n")
            print(algorithms.show(algo_name))

        elif choice == "4":
            print("\n👋 Exiting... Goodbye!\n")
            break

        else:
            print("\n❌ Invalid choice. Please enter 1, 2, 3, or 4.\n")

        input("\n🔁 Press Enter to continue...")  # pause before showing menu again
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
