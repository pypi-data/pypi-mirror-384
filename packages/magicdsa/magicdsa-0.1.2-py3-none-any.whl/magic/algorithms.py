"""
algorithms.py - Core storage for all algorithm code in the 'magic' module.

🔹 How it works:
- Store each algorithm's code as a string in the `algorithms` dictionary.
- Use `show(name)` to display the algorithm code in output.
- Use `list_all()` to see all algorithm names.
- Use `category(cat)` to filter algorithms by category.

You can add new algorithms anytime by inserting them into the correct
dictionary section below.
"""

# ------------------------------
# 📚 ALGORITHMS STORAGE
# ------------------------------

algorithms = {
    # ============================================
    # 1️⃣ ARRAY ALGORITHMS
    # ============================================
    "two_sum": """
# Two Sum - Array Algorithm

def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

# Example:
# nums = [2, 7, 11, 15]
# print(two_sum(nums, 9))  # Output: [0, 1]
""",
 "linearsearch": """
# Linear Search - Searching Algorithm

def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

# Example:
# arr = [2, 4, 6, 8, 10]
# print(linear_search(arr, 8))  # Output: 3
""",

    "binarysearch": """
# Binary Search - Searching Algorithm
# NOTE: Works only on sorted arrays

def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Example:
# arr = [2, 4, 6, 8, 10]
# print(binary_search(arr, 8))  # Output: 3
""",

    "ternarysearch": """
# Ternary Search - Searching Algorithm
# NOTE: Works only on sorted arrays

def ternary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid1 = left + (right - left) // 3
        mid2 = right - (right - left) // 3

        if arr[mid1] == target:
            return mid1
        if arr[mid2] == target:
            return mid2

        if target < arr[mid1]:
            right = mid1 - 1
        elif target > arr[mid2]:
            left = mid2 + 1
        else:
            left = mid1 + 1
            right = mid2 - 1
    return -1

# Example:
# arr = [2, 4, 6, 8, 10]
# print(ternary_search(arr, 8))  # Output: 3
""",

    "bubblesort": """
# Bubble Sort - Sorting Algorithm

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

# Example:
# arr = [64, 34, 25, 12, 22, 11, 90]
# bubble_sort(arr)
# print(arr)  # Output: [11, 12, 22, 25, 34, 64, 90]
""",

    "selectionsort": """
# Selection Sort - Sorting Algorithm

def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]

# Example:
# arr = [64, 25, 12, 22, 11]
# selection_sort(arr)
# print(arr)  # Output: [11, 12, 22, 25, 64]
""",

    "insertionsort": """
# Insertion Sort - Sorting Algorithm

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

# Example:
# arr = [12, 11, 13, 5, 6]
# insertion_sort(arr)
# print(arr)  # Output: [5, 6, 11, 12, 13]
""",
    "mergesort": """
# Merge Sort - Sorting Algorithm
# Time Complexity: O(n log n)

def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        L = arr[:mid]
        R = arr[mid:]

        merge_sort(L)
        merge_sort(R)

        i = j = k = 0

        while i < len(L) and j < len(R):
            if L[i] < R[j]:
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            k += 1

        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1

        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1

# Example:
# arr = [64, 25, 12, 22, 11]
# merge_sort(arr)
# print(arr)  # Output: [11, 12, 22, 25, 64]
""",

    "quicksort": """
# Quick Sort - Sorting Algorithm
# Time Complexity: O(n log n) average

def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# Example:
# arr = [10, 7, 8, 9, 1, 5]
# print(quick_sort(arr))  # Output: [1, 5, 7, 8, 9, 10]
""",

    "countingsort": """
# Counting Sort - Sorting Algorithm
# Works for non-negative integers
# Time Complexity: O(n + k)

def counting_sort(arr):
    if len(arr) == 0:
        return

    max_val = max(arr)
    count = [0] * (max_val + 1)

    for num in arr:
        count[num] += 1

    idx = 0
    for i in range(len(count)):
        while count[i] > 0:
            arr[idx] = i
            idx += 1
            count[i] -= 1

# Example:
# arr = [4, 2, 2, 8, 3, 3, 1]
# counting_sort(arr)
# print(arr)  # Output: [1, 2, 2, 3, 3, 4, 8]
""",

    "radixsort": """
# Radix Sort - Sorting Algorithm
# Works for non-negative integers
# Time Complexity: O(d * (n + k))

def counting_sort_for_radix(arr, exp):
    n = len(arr)
    output = [0] * n
    count = [0] * 10

    for i in range(n):
        index = arr[i] // exp
        count[index % 10] += 1

    for i in range(1, 10):
        count[i] += count[i - 1]

    i = n - 1
    while i >= 0:
        index = arr[i] // exp
        output[count[index % 10] - 1] = arr[i]
        count[index % 10] -= 1
        i -= 1

    for i in range(n):
        arr[i] = output[i]

def radix_sort(arr):
    max_num = max(arr)
    exp = 1
    while max_num // exp > 0:
        counting_sort_for_radix(arr, exp)
        exp *= 10

# Example:
# arr = [170, 45, 75, 90, 802, 24, 2, 66]
# radix_sort(arr)
# print(arr)  # Output: [2, 24, 45, 66, 75, 90, 170, 802]
""",

    "bucketsort": """
# Bucket Sort - Sorting Algorithm
# Best for uniformly distributed floating point numbers
# Time Complexity: O(n + k)

def bucket_sort(arr):
    if len(arr) == 0:
        return

    buckets = [[] for _ in range(len(arr))]

    for num in arr:
        index = int(num * len(arr))
        buckets[index].append(num)

    for bucket in buckets:
        bucket.sort()

    idx = 0
    for bucket in buckets:
        for num in bucket:
            arr[idx] = num
            idx += 1

# Example:
# arr = [0.78, 0.17, 0.39, 0.26, 0.72, 0.94, 0.21, 0.12, 0.23, 0.68]
# bucket_sort(arr)
# print(arr)  # Output: [0.12, 0.17, 0.21, 0.23, 0.26, 0.39, 0.68, 0.72, 0.78, 0.94]
""",

    "maxsumsubarrayofsizek": """
# Maximum Sum Subarray of Size K - Sliding Window Algorithm

def max_sum_subarray_of_size_k(arr, k):
    max_sum = 0
    window_sum = sum(arr[:k])
    max_sum = window_sum

    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)

    return max_sum

# Example:
# arr = [2, 1, 5, 1, 3, 2]
# k = 3
# print(max_sum_subarray_of_size_k(arr, k))  # Output: 9
""",
    "longestsubstringwithkdistinct": """
# Longest Substring with K Distinct Characters - Sliding Window Algorithm
# Time Complexity: O(n)

def longest_substring_with_k_distinct(s, k):
    from collections import defaultdict
    left = 0
    max_len = 0
    char_count = defaultdict(int)

    for right in range(len(s)):
        char_count[s[right]] += 1

        while len(char_count) > k:
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1

        max_len = max(max_len, right - left + 1)

    return max_len

# Example:
# s = "eceba"
# k = 2
# print(longest_substring_with_k_distinct(s, k))  # Output: 3  ("ece")
""",

    "prefixsumarray": """
# Prefix Sum Array - Array Algorithm
# Time Complexity: O(n)

def prefix_sum(arr):
    prefix = [0] * len(arr)
    prefix[0] = arr[0]
    for i in range(1, len(arr)):
        prefix[i] = prefix[i - 1] + arr[i]
    return prefix

# Example:
# arr = [1, 2, 3, 4, 5]
# print(prefix_sum(arr))  # Output: [1, 3, 6, 10, 15]
""",

    "differencearray": """
# Difference Array - Range Update Technique
# Time Complexity: O(1) per update

def apply_range_updates(n, updates):
    diff = [0] * (n + 1)

    for start, end, val in updates:
        diff[start] += val
        if end + 1 < n:
            diff[end + 1] -= val

    arr = [0] * n
    arr[0] = diff[0]
    for i in range(1, n):
        arr[i] = arr[i - 1] + diff[i]
    return arr

# Example:
# n = 5
# updates = [(1, 3, 2), (2, 4, 3)]
# print(apply_range_updates(n, updates))  # Output: [0, 2, 5, 5, 3]
""",

    "kadane": """
# Kadane's Algorithm - Maximum Subarray Sum
# Time Complexity: O(n)

def kadane(arr):
    max_so_far = arr[0]
    current_max = arr[0]
    for i in range(1, len(arr)):
        current_max = max(arr[i], current_max + arr[i])
        max_so_far = max(max_so_far, current_max)
    return max_so_far

# Example:
# arr = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
# print(kadane(arr))  # Output: 6  (subarray [4, -1, 2, 1])
""",

    "spiralmatrix": """
# Spiral Matrix Traversal - Matrix Algorithm
# Time Complexity: O(m * n)

def spiral_order(matrix):
    result = []
    while matrix:
        result += matrix[0]
        matrix = list(zip(*matrix[1:]))[::-1]
    return result

# Example:
# matrix = [
#   [1, 2, 3],
#   [4, 5, 6],
#   [7, 8, 9]
# ]
# print(spiral_order(matrix))  # Output: [1, 2, 3, 6, 9, 8, 7, 4, 5]
""",

    "rotatematrix": """
# Rotate Matrix by 90 Degrees Clockwise - Matrix Algorithm
# Time Complexity: O(n^2)

def rotate_matrix(matrix):
    n = len(matrix)
    # Transpose
    for i in range(n):
        for j in range(i, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # Reverse each row
    for row in matrix:
        row.reverse()
    return matrix

# Example:
# matrix = [
#   [1, 2, 3],
#   [4, 5, 6],
#   [7, 8, 9]
# ]
# print(rotate_matrix(matrix))
# Output:
# [
#   [7, 4, 1],
#   [8, 5, 2],
#   [9, 6, 3]
# ]
""",
    "searchin2dmatrixi": """
# Search in 2D Matrix I - Binary Search on Matrix
# Time Complexity: O(log(m * n))

def search_matrix_I(matrix, target):
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1

    while left <= right:
        mid = (left + right) // 2
        mid_val = matrix[mid // cols][mid % cols]

        if mid_val == target:
            return True
        elif mid_val < target:
            left = mid + 1
        else:
            right = mid - 1
    return False

# Example:
# matrix = [
#   [1, 3, 5, 7],
#   [10, 11, 16, 20],
#   [23, 30, 34, 50]
# ]
# print(search_matrix_I(matrix, 3))  # Output: True
""",

    "searchin2dmatrixii": """
# Search in 2D Matrix II - Optimized Search from Top-Right
# Time Complexity: O(m + n)

def search_matrix_II(matrix, target):
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    row, col = 0, cols - 1

    while row < rows and col >= 0:
        if matrix[row][col] == target:
            return True
        elif matrix[row][col] > target:
            col -= 1
        else:
            row += 1
    return False

# Example:
# matrix = [
#   [1, 4, 7, 11, 15],
#   [2, 5, 8, 12, 19],
#   [3, 6, 9, 16, 22],
#   [10, 13, 14, 17, 24],
#   [18, 21, 23, 26, 30]
# ]
# print(search_matrix_II(matrix, 5))  # Output: True
""",

    "transposematrix": """
# Transpose Matrix - Matrix Transformation
# Time Complexity: O(m * n)

def transpose_matrix(matrix):
    rows, cols = len(matrix), len(matrix[0])
    result = [[0] * rows for _ in range(cols)]
    for i in range(rows):
        for j in range(cols):
            result[j][i] = matrix[i][j]
    return result

# Example:
# matrix = [
#   [1, 2, 3],
#   [4, 5, 6]
# ]
# print(transpose_matrix(matrix))
# Output:
# [
#   [1, 4],
#   [2, 5],
#   [3, 6]
# ]
""",

    "sortcolors": """
# Sort Colors (Dutch National Flag Algorithm)
# Time Complexity: O(n)

def sort_colors(nums):
    low, mid, high = 0, 0, len(nums) - 1
    while mid <= high:
        if nums[mid] == 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1

# Example:
# nums = [2, 0, 2, 1, 1, 0]
# sort_colors(nums)
# print(nums)  # Output: [0, 0, 1, 1, 2, 2]
""",

    "trappingrainwater": """
# Trapping Rain Water - Two Pointer Approach
# Time Complexity: O(n)

def trap(height):
    if not height:
        return 0
    left, right = 0, len(height) - 1
    left_max, right_max = height[left], height[right]
    water = 0

    while left < right:
        if left_max < right_max:
            left += 1
            left_max = max(left_max, height[left])
            water += left_max - height[left]
        else:
            right -= 1
            right_max = max(right_max, height[right])
            water += right_max - height[right]
    return water

# Example:
# height = [0,1,0,2,1,0,1,3,2,1,2,1]
# print(trap(height))  # Output: 6
""",

    "containerwithmostwater": """
# Container With Most Water - Two Pointer Approach
# Time Complexity: O(n)

def max_area(height):
    left, right = 0, len(height) - 1
    max_water = 0
    while left < right:
        width = right - left
        max_water = max(max_water, min(height[left], height[right]) * width)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return max_water

# Example:
# height = [1,8,6,2,5,4,8,3,7]
# print(max_area(height))  # Output: 49
""",

    "jumpgame": """
# Jump Game - Greedy Algorithm
# Time Complexity: O(n)

def can_jump(nums):
    max_reach = 0
    for i, jump in enumerate(nums):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + jump)
    return True

# Example:
# nums = [2,3,1,1,4]
# print(can_jump(nums))  # Output: True
""",
    "minimumplatforms": """
# Minimum Platforms - Greedy Algorithm
# Time Complexity: O(n log n)

def minimum_platforms(arrival, departure):
    arrival.sort()
    departure.sort()

    platform_needed = 1
    result = 1
    i, j = 1, 0
    n = len(arrival)

    while i < n and j < n:
        if arrival[i] <= departure[j]:
            platform_needed += 1
            result = max(result, platform_needed)
            i += 1
        else:
            platform_needed -= 1
            j += 1
    return result

# Example:
# arrival = [900, 940, 950, 1100, 1500, 1800]
# departure = [910, 1200, 1120, 1130, 1900, 2000]
# print(minimum_platforms(arrival, departure))  # Output: 3
""",

    "naivepatternsearch": """
# Naive Pattern Searching Algorithm
# Time Complexity: O((n - m + 1) * m)

def naive_search(text, pattern):
    n = len(text)
    m = len(pattern)
    positions = []

    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            positions.append(i)
    return positions

# Example:
# text = "AABAACAADAABAABA"
# pattern = "AABA"
# print(naive_search(text, pattern))  # Output: [0, 9, 12]
""",

    "kmpalgorithm": """
# KMP (Knuth-Morris-Pratt) Pattern Searching Algorithm
# Time Complexity: O(n + m)

def compute_lps(pattern):
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps

def kmp_search(text, pattern):
    n = len(text)
    m = len(pattern)
    lps = compute_lps(pattern)
    i = j = 0
    positions = []

    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            positions.append(i - j)
            j = lps[j - 1]
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return positions

# Example:
# text = "ABABDABACDABABCABAB"
# pattern = "ABABCABAB"
# print(kmp_search(text, pattern))  # Output: [10]
""",

    "rabinkarp": """
# Rabin-Karp Pattern Searching Algorithm
# Time Complexity: O((n - m + 1) * m) worst case, O(n + m) average

def rabin_karp(text, pattern, q=101):
    n = len(text)
    m = len(pattern)
    d = 256
    p = 0  # hash value for pattern
    t = 0  # hash value for text
    h = 1
    positions = []

    for i in range(m - 1):
        h = (h * d) % q

    for i in range(m):
        p = (d * p + ord(pattern[i])) % q
        t = (d * t + ord(text[i])) % q

    for i in range(n - m + 1):
        if p == t:
            if text[i:i + m] == pattern:
                positions.append(i)
        if i < n - m:
            t = (d * (t - ord(text[i]) * h) + ord(text[i + m])) % q
            if t < 0:
                t += q
    return positions

# Example:
# text = "GEEKS FOR GEEKS"
# pattern = "GEEK"
# print(rabin_karp(text, pattern))  # Output: [0, 10]
""",

    "zalgorithm": """
# Z-Algorithm for Pattern Matching
# Time Complexity: O(n + m)

def calculate_z_array(s):
    n = len(s)
    Z = [0] * n
    l, r = 0, 0

    for i in range(1, n):
        if i <= r:
            Z[i] = min(r - i + 1, Z[i - l])
        while i + Z[i] < n and s[Z[i]] == s[i + Z[i]]:
            Z[i] += 1
        if i + Z[i] - 1 > r:
            l, r = i, i + Z[i] - 1
    return Z

def z_algorithm_search(text, pattern):
    concat = pattern + "$" + text
    Z = calculate_z_array(concat)
    result = []

    for i in range(len(Z)):
        if Z[i] == len(pattern):
            result.append(i - len(pattern) - 1)
    return result

# Example:
# text = "aabxaabxcaabxaabxay"
# pattern = "aabx"
# print(z_algorithm_search(text, pattern))  # Output: [0, 4, 9, 13]
""",
# ============================================
    # 3️⃣ LINKED LIST ALGORITHMS
    # ============================================
    # "reverse_linked_list": """...""",
    # "detect_cycle": """...""",
    "singlylinkedlist": """
# Singly Linked List Operations - Create, Insert, Delete, Display

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class SinglyLinkedList:
    def __init__(self):
        self.head = None

    def insert_at_end(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        temp = self.head
        while temp.next:
            temp = temp.next
        temp.next = new_node

    def delete_node(self, key):
        temp = self.head

        if temp and temp.data == key:
            self.head = temp.next
            temp = None
            return

        prev = None
        while temp and temp.data != key:
            prev = temp
            temp = temp.next

        if temp is None:
            return
        prev.next = temp.next
        temp = None

    def display(self):
        temp = self.head
        while temp:
            print(temp.data, end=" -> ")
        print("None")

# Example:
# ll = SinglyLinkedList()
# ll.insert_at_end(1)
# ll.insert_at_end(2)
# ll.insert_at_end(3)
# ll.display()  # Output: 1 -> 2 -> 3 -> None
# ll.delete_node(2)
# ll.display()  # Output: 1 -> 3 -> None
""",

    "doublylinkedlist": """
# Doubly Linked List Operations - Insert, Delete, Display

class DNode:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None

    def insert_at_end(self, data):
        new_node = DNode(data)
        if not self.head:
            self.head = new_node
            return
        temp = self.head
        while temp.next:
            temp = temp.next
        temp.next = new_node
        new_node.prev = temp

    def delete_node(self, key):
        temp = self.head
        while temp and temp.data != key:
            temp = temp.next
        if temp is None:
            return
        if temp.prev:
            temp.prev.next = temp.next
        if temp.next:
            temp.next.prev = temp.prev
        if temp == self.head:
            self.head = temp.next
        temp = None

    def display(self):
        temp = self.head
        while temp:
            print(temp.data, end=" <-> ")
            temp = temp.next
        print("None")

# Example:
# dll = DoublyLinkedList()
# dll.insert_at_end(1)
# dll.insert_at_end(2)
# dll.insert_at_end(3)
# dll.display()  # Output: 1 <-> 2 <-> 3 <-> None
# dll.delete_node(2)
# dll.display()  # Output: 1 <-> 3 <-> None
""",

    "circularlinkedlist": """
# Circular Linked List - Insert and Display

class CNode:
    def __init__(self, data):
        self.data = data
        self.next = None

class CircularLinkedList:
    def __init__(self):
        self.head = None

    def insert(self, data):
        new_node = CNode(data)
        if not self.head:
            self.head = new_node
            new_node.next = self.head
            return
        temp = self.head
        while temp.next != self.head:
            temp = temp.next
        temp.next = new_node
        new_node.next = self.head

    def display(self):
        if not self.head:
            return
        temp = self.head
        while True:
            print(temp.data, end=" -> ")
            temp = temp.next
            if temp == self.head:
                break
        print("(head)")

# Example:
# cll = CircularLinkedList()
# cll.insert(10)
# cll.insert(20)
# cll.insert(30)
# cll.display()  # Output: 10 -> 20 -> 30 -> (head)
""",

    "reverselinkedlist": """
# Reverse a Singly Linked List - Iterative Approach
# Time Complexity: O(n)

class NodeRev:
    def __init__(self, data):
        self.data = data
        self.next = None

def reverse_linked_list(head):
    prev = None
    current = head
    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node
    return prev

# Example:
# head = NodeRev(1)
# head.next = NodeRev(2)
# head.next.next = NodeRev(3)
# new_head = reverse_linked_list(head)
# temp = new_head
# while temp:
#     print(temp.data, end=" -> ")  # Output: 3 -> 2 -> 1 ->
""",

    "detectandremoveloop": """
# Detect and Remove Loop in a Linked List - Floyd's Cycle Detection
# Time Complexity: O(n)

class LoopNode:
    def __init__(self, data):
        self.data = data
        self.next = None

def detect_and_remove_loop(head):
    slow = fast = head

    # Detect loop
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            break

    # No loop
    if fast is None or fast.next is None:
        return False

    # Find loop start
    slow = head
    while slow.next != fast.next:
        slow = slow.next
        fast = fast.next

    # Remove loop
    fast.next = None
    return True

# Example:
# head = LoopNode(1)
# head.next = LoopNode(2)
# head.next.next = LoopNode(3)
# head.next.next.next = head.next  # Loop
# detect_and_remove_loop(head)  # Loop removed
""",

    "mergetwosortedlists": """
# Merge Two Sorted Linked Lists - Iterative Approach
# Time Complexity: O(n + m)

class MergeNode:
    def __init__(self, data):
        self.data = data
        self.next = None

def merge_two_sorted_lists(l1, l2):
    dummy = MergeNode(0)
    tail = dummy

    while l1 and l2:
        if l1.data < l2.data:
            tail.next = l1
            l1 = l1.next
        else:
            tail.next = l2
            l2 = l2.next
        tail = tail.next

    tail.next = l1 or l2
    return dummy.next

# Example:
# a = MergeNode(1)
# a.next = MergeNode(3)
# a.next.next = MergeNode(5)
# b = MergeNode(2)
# b.next = MergeNode(4)
# merged = merge_two_sorted_lists(a, b)
# while merged:
#     print(merged.data, end=" -> ")  # Output: 1 -> 2 -> 3 -> 4 -> 5 ->
""",
    "addtwonumbers": """
# Add Two Numbers Represented by Linked Lists
# Time Complexity: O(max(m, n))

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def add_two_numbers(l1, l2):
    dummy = ListNode(0)
    current = dummy
    carry = 0

    while l1 or l2 or carry:
        val1 = l1.val if l1 else 0
        val2 = l2.val if l2 else 0
        total = val1 + val2 + carry
        carry = total // 10
        current.next = ListNode(total % 10)
        current = current.next

        if l1: l1 = l1.next
        if l2: l2 = l2.next

    return dummy.next

# Example:
# a = ListNode(2, ListNode(4, ListNode(3)))
# b = ListNode(5, ListNode(6, ListNode(4)))
# result = add_two_numbers(a, b)
# while result:
#     print(result.val, end=" -> ")  # Output: 7 -> 0 -> 8 ->
""",

    "copylistwithrandompointer": """
# Copy List with Random Pointer - HashMap Method
# Time Complexity: O(n)

class RandomNode:
    def __init__(self, val=0, next=None, random=None):
        self.val = val
        self.next = next
        self.random = random

def copy_random_list(head):
    if not head:
        return None

    old_to_new = {}
    current = head

    # First pass: clone nodes
    while current:
        old_to_new[current] = RandomNode(current.val)
        current = current.next

    # Second pass: assign next and random pointers
    current = head
    while current:
        old_to_new[current].next = old_to_new.get(current.next)
        old_to_new[current].random = old_to_new.get(current.random)
        current = current.next

    return old_to_new[head]

# Example:
# Node structure: [val | next | random]
# list copied with identical structure and random pointers
""",

    "lrucache": """
# LRU (Least Recently Used) Cache Implementation - Using OrderedDict
# Time Complexity: O(1) for get and put

from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

# Example:
# lru = LRUCache(2)
# lru.put(1, 1)
# lru.put(2, 2)
# print(lru.get(1))  # Output: 1
# lru.put(3, 3)      # Evicts key 2
# print(lru.get(2))  # Output: -1
""",

    "intersectionoftwolls": """
# Intersection of Two Linked Lists - Two Pointer Approach
# Time Complexity: O(m + n)

class IntNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def get_intersection_node(headA, headB):
    if not headA or not headB:
        return None

    a, b = headA, headB
    while a != b:
        a = a.next if a else headB
        b = b.next if b else headA
    return a

# Example:
# A: 4 -> 1 -> 8 -> 4 -> 5
# B: 5 -> 6 -> 1 -> 8 -> 4 -> 5
# print(get_intersection_node(headA, headB).val)  # Output: 8
""",

    "sortlinkedlistmergesort": """
# Sort Linked List using Merge Sort
# Time Complexity: O(n log n)

class SortNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def merge_sorted_lists(l1, l2):
    dummy = SortNode(0)
    tail = dummy
    while l1 and l2:
        if l1.val < l2.val:
            tail.next = l1
            l1 = l1.next
        else:
            tail.next = l2
            l2 = l2.next
        tail = tail.next
    tail.next = l1 or l2
    return dummy.next

def get_middle(head):
    slow = head
    fast = head.next
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow

def sort_linked_list(head):
    if not head or not head.next:
        return head
    mid = get_middle(head)
    right_head = mid.next
    mid.next = None
    left = sort_linked_list(head)
    right = sort_linked_list(right_head)
    return merge_sorted_lists(left, right)

# Example:
# head = SortNode(4, SortNode(2, SortNode(1, SortNode(3))))
# sorted_head = sort_linked_list(head)
# while sorted_head:
#     print(sorted_head.val, end=" -> ")  # Output: 1 -> 2 -> 3 -> 4 ->
""",
 # ============================================
    # 4️⃣ STACK & QUEUE ALGORITHMS
    # ============================================
    # "valid_parentheses": """...""",
    # "min_stack": """...""",
    "implementstack": """
# Implement Stack using List
# Time Complexity: O(1) for push and pop

class Stack:
    def __init__(self):
        self.stack = []

    def push(self, val):
        self.stack.append(val)

    def pop(self):
        if not self.is_empty():
            return self.stack.pop()
        return None

    def peek(self):
        if not self.is_empty():
            return self.stack[-1]
        return None

    def is_empty(self):
        return len(self.stack) == 0

# Example:
# s = Stack()
# s.push(10)
# s.push(20)
# print(s.pop())   # Output: 20
# print(s.peek())  # Output: 10
""",

    "stackusingtwoqueues": """
# Stack using Two Queues
# Push: O(n), Pop: O(1)

from collections import deque

class StackUsingQueues:
    def __init__(self):
        self.q1 = deque()
        self.q2 = deque()

    def push(self, x):
        self.q2.append(x)
        while self.q1:
            self.q2.append(self.q1.popleft())
        self.q1, self.q2 = self.q2, self.q1

    def pop(self):
        if self.q1:
            return self.q1.popleft()
        return None

    def top(self):
        return self.q1[0] if self.q1 else None

    def is_empty(self):
        return len(self.q1) == 0

# Example:
# s = StackUsingQueues()
# s.push(1)
# s.push(2)
# print(s.top())  # Output: 2
# print(s.pop())  # Output: 2
""",

    "queueusingtwostacks": """
# Queue using Two Stacks
# Amortized Time Complexity: O(1) per operation

class QueueUsingStacks:
    def __init__(self):
        self.stack1 = []
        self.stack2 = []

    def enqueue(self, x):
        self.stack1.append(x)

    def dequeue(self):
        if not self.stack2:
            while self.stack1:
                self.stack2.append(self.stack1.pop())
        if self.stack2:
            return self.stack2.pop()
        return None

    def front(self):
        if not self.stack2:
            while self.stack1:
                self.stack2.append(self.stack1.pop())
        return self.stack2[-1] if self.stack2 else None

# Example:
# q = QueueUsingStacks()
# q.enqueue(10)
# q.enqueue(20)
# print(q.dequeue())  # Output: 10
# print(q.front())    # Output: 20
""",

    "balancedparentheses": """
# Balanced Parentheses Checker - Stack Approach
# Time Complexity: O(n)

def is_balanced(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping:
            if not stack or stack.pop() != mapping[char]:
                return False
    return not stack

# Example:
# s = "({[]})"
# print(is_balanced(s))  # Output: True
# s = "([)]"
# print(is_balanced(s))  # Output: False
""",

    "nextgreaterelement": """
# Next Greater Element - Stack Approach
# Time Complexity: O(n)

def next_greater_element(arr):
    result = [-1] * len(arr)
    stack = []

    for i in range(len(arr) - 1, -1, -1):
        while stack and stack[-1] <= arr[i]:
            stack.pop()
        if stack:
            result[i] = stack[-1]
        stack.append(arr[i])

    return result

# Example:
# arr = [4, 5, 2, 25]
# print(next_greater_element(arr))  # Output: [5, 25, 25, -1]
""",

    "dailytemperatures": """
# Daily Temperatures - Monotonic Stack
# Time Complexity: O(n)

def daily_temperatures(temperatures):
    res = [0] * len(temperatures)
    stack = []  # stores indices

    for i, temp in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < temp:
            idx = stack.pop()
            res[idx] = i - idx
        stack.append(i)
    return res

# Example:
# temps = [73, 74, 75, 71, 69, 72, 76, 73]
# print(daily_temperatures(temps))  # Output: [1, 1, 4, 2, 1, 1, 0, 0]
""",
    "minstack": """
# Min Stack - Stack with O(1) getMin()
# Time Complexity: O(1) for push, pop, top, getMin

class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, val):
        self.stack.append(val)
        if not self.min_stack or val <= self.min_stack[-1]:
            self.min_stack.append(val)

    def pop(self):
        if self.stack:
            val = self.stack.pop()
            if val == self.min_stack[-1]:
                self.min_stack.pop()

    def top(self):
        return self.stack[-1] if self.stack else None

    def get_min(self):
        return self.min_stack[-1] if self.min_stack else None

# Example:
# s = MinStack()
# s.push(3)
# s.push(5)
# s.push(2)
# print(s.get_min())  # Output: 2
# s.pop()
# print(s.get_min())  # Output: 3
""",

    "infixtopostfix": """
# Infix to Postfix Conversion - Shunting Yard Algorithm
# Time Complexity: O(n)

def infix_to_postfix(expression):
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    output = []
    stack = []

    for char in expression:
        if char.isalnum():
            output.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        else:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence[char]:
                output.append(stack.pop())
            stack.append(char)

    while stack:
        output.append(stack.pop())

    return "".join(output)

# Example:
# expr = "A*(B+C)/D"
# print(infix_to_postfix(expr))  # Output: ABC+*D/
""",

    "evaluatepostfix": """
# Evaluate Postfix Expression - Stack Approach
# Time Complexity: O(n)

def evaluate_postfix(expression):
    stack = []
    for char in expression:
        if char.isdigit():
            stack.append(int(char))
        else:
            b = stack.pop()
            a = stack.pop()
            if char == '+':
                stack.append(a + b)
            elif char == '-':
                stack.append(a - b)
            elif char == '*':
                stack.append(a * b)
            elif char == '/':
                stack.append(int(a / b))
    return stack.pop()

# Example:
# expr = "231*+9-"
# print(evaluate_postfix(expr))  # Output: -4
""",

    "monotonicstack": """
# Monotonic Stack - Generic Example (Next Greater Element)
# Time Complexity: O(n)

def monotonic_stack(arr):
    stack = []
    result = [-1] * len(arr)

    for i in range(len(arr) - 1, -1, -1):
        while stack and stack[-1] <= arr[i]:
            stack.pop()
        if stack:
            result[i] = stack[-1]
        stack.append(arr[i])

    return result

# Example:
# arr = [2, 1, 2, 4, 3]
# print(monotonic_stack(arr))  # Output: [4, 2, 4, -1, -1]
""",

    "slidingwindowmaximum": """
# Sliding Window Maximum - Monotonic Deque
# Time Complexity: O(n)

from collections import deque

def sliding_window_maximum(nums, k):
    dq = deque()
    result = []

    for i, num in enumerate(nums):
        # Remove indices outside the window
        if dq and dq[0] == i - k:
            dq.popleft()
        # Remove smaller elements from the back
        while dq and nums[dq[-1]] < num:
            dq.pop()
        dq.append(i)
        # Append max for current window
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result

# Example:
# nums = [1,3,-1,-3,5,3,6,7]
# k = 3
# print(sliding_window_maximum(nums, k))  # Output: [3,3,5,5,6,7]
""",
    "towerofhanoi": """
# Tower of Hanoi - Classic Recursive Algorithm
# Time Complexity: O(2^n)

def tower_of_hanoi(n, source, target, auxiliary):
    if n == 1:
        print(f"Move disk 1 from {source} to {target}")
        return
    tower_of_hanoi(n - 1, source, auxiliary, target)
    print(f"Move disk {n} from {source} to {target}")
    tower_of_hanoi(n - 1, auxiliary, target, source)

# Example:
# tower_of_hanoi(3, 'A', 'C', 'B')
# Output:
# Move disk 1 from A to C
# Move disk 2 from A to B
# Move disk 1 from C to B
# Move disk 3 from A to C
# Move disk 1 from B to A
# Move disk 2 from B to C
# Move disk 1 from A to C
""",

    "subsets": """
# Generate All Subsets - Backtracking
# Time Complexity: O(2^n)

def subsets(nums):
    result = []

    def backtrack(start, path):
        result.append(path[:])
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()

    backtrack(0, [])
    return result

# Example:
# nums = [1, 2, 3]
# print(subsets(nums))
# Output: [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
""",

    "permutations": """
# Generate All Permutations - Backtracking
# Time Complexity: O(n!)

def permutations(nums):
    result = []

    def backtrack(path, remaining):
        if not remaining:
            result.append(path[:])
            return
        for i in range(len(remaining)):
            backtrack(path + [remaining[i]], remaining[:i] + remaining[i + 1:])

    backtrack([], nums)
    return result

# Example:
# nums = [1, 2, 3]
# print(permutations(nums))
# Output: [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
""",

    "combinationsum": """
# Combination Sum - Backtracking
# Time Complexity: O(2^t) (t = target)

def combination_sum(candidates, target):
    result = []

    def backtrack(start, path, total):
        if total == target:
            result.append(path[:])
            return
        if total > target:
            return
        for i in range(start, len(candidates)):
            path.append(candidates[i])
            backtrack(i, path, total + candidates[i])
            path.pop()

    backtrack(0, [], 0)
    return result

# Example:
# candidates = [2, 3, 6, 7]
# target = 7
# print(combination_sum(candidates, target))
# Output: [[2, 2, 3], [7]]
""",

    "palindromepartitioning": """
# Palindrome Partitioning - Backtracking
# Time Complexity: O(2^n)

def palindrome_partitioning(s):
    result = []

    def is_palindrome(sub):
        return sub == sub[::-1]

    def backtrack(start, path):
        if start == len(s):
            result.append(path[:])
            return
        for end in range(start + 1, len(s) + 1):
            substring = s[start:end]
            if is_palindrome(substring):
                path.append(substring)
                backtrack(end, path)
                path.pop()

    backtrack(0, [])
    return result

# Example:
# s = "aab"
# print(palindrome_partitioning(s))
# Output: [['a', 'a', 'b'], ['aa', 'b']]
""",

    "wordsearch": """
# Word Search in 2D Grid - Backtracking
# Time Complexity: O(m * n * 4^L)

def exist(board, word):
    rows, cols = len(board), len(board[0])
    path = set()

    def dfs(r, c, i):
        if i == len(word):
            return True
        if (r < 0 or c < 0 or r >= rows or c >= cols or 
            word[i] != board[r][c] or (r, c) in path):
            return False

        path.add((r, c))
        res = (dfs(r + 1, c, i + 1) or 
               dfs(r - 1, c, i + 1) or 
               dfs(r, c + 1, i + 1) or 
               dfs(r, c - 1, i + 1))
        path.remove((r, c))
        return res

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False

# Example:
# board = [
#   ['A','B','C','E'],
#   ['S','F','C','S'],
#   ['A','D','E','E']
# ]
# word = "ABCCED"
# print(exist(board, word))  # Output: True
""",
    "nqueens": """
# N-Queens - Backtracking
# Time Complexity: O(N!)

def solve_n_queens(n):
    board = [["."] * n for _ in range(n)]
    result = []

    def is_safe(row, col):
        # Check column
        for i in range(row):
            if board[i][col] == "Q":
                return False
        # Check left diagonal
        i, j = row - 1, col - 1
        while i >= 0 and j >= 0:
            if board[i][j] == "Q":
                return False
            i -= 1
            j -= 1
        # Check right diagonal
        i, j = row - 1, col + 1
        while i >= 0 and j < n:
            if board[i][j] == "Q":
                return False
            i -= 1
            j += 1
        return True

    def backtrack(row):
        if row == n:
            result.append(["".join(r) for r in board])
            return
        for col in range(n):
            if is_safe(row, col):
                board[row][col] = "Q"
                backtrack(row + 1)
                board[row][col] = "."

    backtrack(0)
    return result

# Example:
# print(solve_n_queens(4))
# Output: [
#   ['.Q..', '...Q', 'Q...', '..Q.'],
#   ['..Q.', 'Q...', '...Q', '.Q..']
# ]
""",

    "sudokusolver": """
# Sudoku Solver - Backtracking
# Time Complexity: O(9^(n*n)) (worst case)

def solve_sudoku(board):
    def is_valid(r, c, num):
        # Row & column check
        for i in range(9):
            if board[r][i] == num or board[i][c] == num:
                return False
        # 3x3 sub-box check
        start_row, start_col = 3 * (r // 3), 3 * (c // 3)
        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if board[i][j] == num:
                    return False
        return True

    def backtrack():
        for i in range(9):
            for j in range(9):
                if board[i][j] == '.':
                    for num in '123456789':
                        if is_valid(i, j, num):
                            board[i][j] = num
                            if backtrack():
                                return True
                            board[i][j] = '.'
                    return False
        return True

    backtrack()
    return board

# Example:
# board = [
#   ["5","3",".",".","7",".",".",".","."],
#   ["6",".",".","1","9","5",".",".","."],
#   [".","9","8",".",".",".",".","6","."],
#   ["8",".",".",".","6",".",".",".","3"],
#   ["4",".",".","8",".","3",".",".","1"],
#   ["7",".",".",".","2",".",".",".","6"],
#   [".","6",".",".",".",".","2","8","."],
#   [".",".",".","4","1","9",".",".","5"],
#   [".",".",".",".","8",".",".","7","9"]
# ]
# solve_sudoku(board)
# for row in board: print(row)
""",

    "generateparentheses": """
# Generate Parentheses - Backtracking
# Time Complexity: O(2^2n)

def generate_parentheses(n):
    result = []

    def backtrack(current, open_count, close_count):
        if len(current) == 2 * n:
            result.append(current)
            return
        if open_count < n:
            backtrack(current + "(", open_count + 1, close_count)
        if close_count < open_count:
            backtrack(current + ")", open_count, close_count + 1)

    backtrack("", 0, 0)
    return result

# Example:
# print(generate_parentheses(3))
# Output: ['((()))', '(()())', '(())()', '()(())', '()()()']
""",

    "ratinamaze": """
# Rat in a Maze - Backtracking
# Time Complexity: O(2^(n^2))

def rat_in_maze(maze):
    n = len(maze)
    result = []
    path = [[0] * n for _ in range(n)]

    def solve(x, y):
        if x == n - 1 and y == n - 1 and maze[x][y] == 1:
            path[x][y] = 1
            result.append([row[:] for row in path])
            path[x][y] = 0
            return

        if 0 <= x < n and 0 <= y < n and maze[x][y] == 1 and path[x][y] == 0:
            path[x][y] = 1
            solve(x + 1, y)  # Down
            solve(x, y + 1)  # Right
            solve(x - 1, y)  # Up
            solve(x, y - 1)  # Left
            path[x][y] = 0

    solve(0, 0)
    return result

# Example:
# maze = [
#   [1, 0, 0, 0],
#   [1, 1, 0, 1],
#   [0, 1, 0, 0],
#   [1, 1, 1, 1]
# ]
# print(rat_in_maze(maze))
""",

    "lettercombinationsofphonenumber": """
# Letter Combinations of a Phone Number - Backtracking
# Time Complexity: O(4^n)

def letter_combinations(digits):
    if not digits:
        return []
    phone_map = {
        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'
    }
    result = []

    def backtrack(index, path):
        if index == len(digits):
            result.append(path)
            return
        for letter in phone_map[digits[index]]:
            backtrack(index + 1, path + letter)

    backtrack(0, "")
    return result

# Example:
# digits = "23"
# print(letter_combinations(digits))
# Output: ['ad', 'ae', 'af', 'bd', 'be', 'bf', 'cd', 'ce', 'cf']
""",
    "treetraversals": """
# Tree Traversals - Inorder, Preorder, Postorder (Recursive & Iterative)
# Time Complexity: O(n)

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# Inorder Traversal (Left, Root, Right)
def inorder(root):
    return inorder(root.left) + [root.val] + inorder(root.right) if root else []

# Preorder Traversal (Root, Left, Right)
def preorder(root):
    return [root.val] + preorder(root.left) + preorder(root.right) if root else []

# Postorder Traversal (Left, Right, Root)
def postorder(root):
    return postorder(root.left) + postorder(root.right) + [root.val] if root else []

# Level Order Traversal (BFS)
from collections import deque
def level_order(root):
    if not root: return []
    result, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        result.append(node.val)
        if node.left: queue.append(node.left)
        if node.right: queue.append(node.right)
    return result

# Example:
# root = TreeNode(1, TreeNode(2), TreeNode(3))
# print(inorder(root))   # [2, 1, 3]
# print(preorder(root))  # [1, 2, 3]
# print(postorder(root)) # [2, 3, 1]
# print(level_order(root)) # [1, 2, 3]
""",

    "treeviews": """
# Binary Tree Views - Top, Bottom, Left, Right
# Time Complexity: O(n)

from collections import deque, defaultdict

# Top View
def top_view(root):
    if not root: return []
    q = deque([(root, 0)])
    hd_map = {}
    while q:
        node, hd = q.popleft()
        if hd not in hd_map:
            hd_map[hd] = node.val
        if node.left: q.append((node.left, hd - 1))
        if node.right: q.append((node.right, hd + 1))
    return [hd_map[key] for key in sorted(hd_map)]

# Bottom View
def bottom_view(root):
    if not root: return []
    q = deque([(root, 0)])
    hd_map = {}
    while q:
        node, hd = q.popleft()
        hd_map[hd] = node.val
        if node.left: q.append((node.left, hd - 1))
        if node.right: q.append((node.right, hd + 1))
    return [hd_map[key] for key in sorted(hd_map)]

# Left View
def left_view(root):
    if not root: return []
    q = deque([root])
    res = []
    while q:
        size = len(q)
        for i in range(size):
            node = q.popleft()
            if i == 0:
                res.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
    return res

# Right View
def right_view(root):
    if not root: return []
    q = deque([root])
    res = []
    while q:
        size = len(q)
        for i in range(size):
            node = q.popleft()
            if i == size - 1:
                res.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
    return res
""",

    "heightdepth": """
# Height / Depth of a Binary Tree - Recursive
# Time Complexity: O(n)

def height(root):
    if not root:
        return 0
    return 1 + max(height(root.left), height(root.right))

# Example:
# print(height(root))
""",

    "diameteroftree": """
# Diameter of Binary Tree - Longest Path Between Two Nodes
# Time Complexity: O(n)

def diameter(root):
    diameter_result = [0]

    def dfs(node):
        if not node:
            return 0
        left = dfs(node.left)
        right = dfs(node.right)
        diameter_result[0] = max(diameter_result[0], left + right)
        return 1 + max(left, right)

    dfs(root)
    return diameter_result[0]

# Example:
# print(diameter(root))
""",

    "balancedtree": """
# Check if a Binary Tree is Height-Balanced
# Time Complexity: O(n)

def is_balanced(root):
    def check(node):
        if not node:
            return 0
        left = check(node.left)
        if left == -1: return -1
        right = check(node.right)
        if right == -1: return -1
        if abs(left - right) > 1: return -1
        return 1 + max(left, right)

    return check(root) != -1
""",

    "mirrortree": """
# Mirror (Invert) a Binary Tree - Recursive
# Time Complexity: O(n)

def mirror_tree(root):
    if not root:
        return None
    root.left, root.right = mirror_tree(root.right), mirror_tree(root.left)
    return root
""",

    "buildtree": """
# Build Tree from Inorder and Preorder
# Time Complexity: O(n)

def build_tree(preorder, inorder):
    if not preorder or not inorder:
        return None
    root_val = preorder[0]
    root = TreeNode(root_val)
    mid = inorder.index(root_val)
    root.left = build_tree(preorder[1:mid + 1], inorder[:mid])
    root.right = build_tree(preorder[mid + 1:], inorder[mid + 1:])
    return root
""",

    "serializedeserialize": """
# Serialize and Deserialize Binary Tree
# Time Complexity: O(n)

def serialize(root):
    res = []
    def dfs(node):
        if not node:
            res.append("None")
            return
        res.append(str(node.val))
        dfs(node.left)
        dfs(node.right)
    dfs(root)
    return ",".join(res)

def deserialize(data):
    vals = iter(data.split(","))
    def dfs():
        val = next(vals)
        if val == "None":
            return None
        node = TreeNode(int(val))
        node.left = dfs()
        node.right = dfs()
        return node
    return dfs()
""",

    "boundarytraversal": """
# Boundary Traversal of Binary Tree - Anti-clockwise
# Time Complexity: O(n)

def boundary_traversal(root):
    if not root: return []

    def left_boundary(node):
        if node and (node.left or node.right):
            res.append(node.val)
            left_boundary(node.left or node.right)

    def right_boundary(node):
        if node and (node.left or node.right):
            right_boundary(node.right or node.left)
            res.append(node.val)

    def leaves(node):
        if node:
            leaves(node.left)
            if not node.left and not node.right:
                res.append(node.val)
            leaves(node.right)

    res = [root.val]
    left_boundary(root.left)
    leaves(root.left)
    leaves(root.right)
    right_boundary(root.right)
    return res
""",

    "burntree": """
# Burn Tree from a Target Node - BFS + Parent Map
# Time Complexity: O(n)

from collections import deque

def min_time_to_burn(root, target):
    if not root: return 0

    # Step 1: Build parent map
    parent = {}
    def dfs(node, par=None):
        if not node: return
        parent[node] = par
        dfs(node.left, node)
        dfs(node.right, node)
    dfs(root)

    # Step 2: Find target node
    def find(node, val):
        if not node: return None
        if node.val == val: return node
        return find(node.left, val) or find(node.right, val)
    start = find(root, target)

    # Step 3: BFS for burning
    visited = set()
    q = deque([(start, 0)])
    visited.add(start)
    max_time = 0

    while q:
        node, time = q.popleft()
        max_time = max(max_time, time)
        for nei in [node.left, node.right, parent[node]]:
            if nei and nei not in visited:
                visited.add(nei)
                q.append((nei, time + 1))
    return max_time
""",

    "lca": """
# Lowest Common Ancestor (LCA) - Recursive
# Time Complexity: O(n)

def lowest_common_ancestor(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    if left and right:
        return root
    return left if left else right
""",

    "flattenbinarytree": """
# Flatten Binary Tree to Linked List (Preorder)
# Time Complexity: O(n)

def flatten(root):
    if not root: return None

    def dfs(node):
        if not node: return None
        left_tail = dfs(node.left)
        right_tail = dfs(node.right)

        if left_tail:
            left_tail.right = node.right
            node.right = node.left
            node.left = None

        return right_tail or left_tail or node

    dfs(root)
""",
    "verticalordertraversal": """
# Vertical Order Traversal of a Binary Tree
# Time Complexity: O(n log n) due to sorting

from collections import defaultdict, deque

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def vertical_order_traversal(root):
    if not root:
        return []

    # Dictionary: column -> list of (row, value)
    col_table = defaultdict(list)
    q = deque([(root, 0, 0)])  # node, row, column

    while q:
        node, row, col = q.popleft()
        col_table[col].append((row, node.val))
        if node.left:
            q.append((node.left, row + 1, col - 1))
        if node.right:
            q.append((node.right, row + 1, col + 1))

    # Sort columns and values within each column
    result = []
    for col in sorted(col_table.keys()):
        col_table[col].sort()  # sort by row first, then value
        column_values = [val for row, val in col_table[col]]
        result.append(column_values)

    return result

# Example:
# root = TreeNode(3)
# root.left = TreeNode(9)
# root.right = TreeNode(20)
# root.right.left = TreeNode(15)
# root.right.right = TreeNode(7)
# print(vertical_order_traversal(root))
# Output: [[9], [3, 15], [20], [7]]
""",
    "bstsearchinsertdelete": """
# BST - Search, Insert, Delete
# Time Complexity: O(h) where h = height of BST

class BSTNode:
    def __init__(self, val=0):
        self.val = val
        self.left = None
        self.right = None

# Search
def bst_search(root, key):
    if not root or root.val == key:
        return root
    if key < root.val:
        return bst_search(root.left, key)
    else:
        return bst_search(root.right, key)

# Insert
def bst_insert(root, key):
    if not root:
        return BSTNode(key)
    if key < root.val:
        root.left = bst_insert(root.left, key)
    else:
        root.right = bst_insert(root.right, key)
    return root

# Delete
def bst_delete(root, key):
    if not root:
        return None
    if key < root.val:
        root.left = bst_delete(root.left, key)
    elif key > root.val:
        root.right = bst_delete(root.right, key)
    else:
        # Node with one or no child
        if not root.left:
            return root.right
        elif not root.right:
            return root.left
        # Node with two children: get inorder successor
        succ = root.right
        while succ.left:
            succ = succ.left
        root.val = succ.val
        root.right = bst_delete(root.right, succ.val)
    return root

# Example:
# root = None
# root = bst_insert(root, 5)
# root = bst_insert(root, 3)
# root = bst_insert(root, 7)
# print(bst_search(root, 3).val)  # Output: 3
# root = bst_delete(root, 3)
""",

    "validatebst": """
# Validate Binary Search Tree - Recursive
# Time Complexity: O(n)

def is_valid_bst(root, min_val=float('-inf'), max_val=float('inf')):
    if not root:
        return True
    if not (min_val < root.val < max_val):
        return False
    return (is_valid_bst(root.left, min_val, root.val) and
            is_valid_bst(root.right, root.val, max_val))
""",

    "kthsmallestlargest": """
# Kth Smallest & Kth Largest in BST - Inorder Traversal
# Time Complexity: O(n)

def kth_smallest(root, k):
    stack = []
    while True:
        while root:
            stack.append(root)
            root = root.left
        root = stack.pop()
        k -= 1
        if k == 0:
            return root.val
        root = root.right

def kth_largest(root, k):
    stack = []
    while True:
        while root:
            stack.append(root)
            root = root.right
        root = stack.pop()
        k -= 1
        if k == 0:
            return root.val
        root = root.left
""",

    "lcainbst": """
# Lowest Common Ancestor in BST
# Time Complexity: O(h)

def lca_in_bst(root, p, q):
    if not root:
        return None
    if p.val < root.val and q.val < root.val:
        return lca_in_bst(root.left, p, q)
    if p.val > root.val and q.val > root.val:
        return lca_in_bst(root.right, p, q)
    return root
""",

    "converttobst": """
# Convert Sorted Array to Balanced BST
# Time Complexity: O(n)

def sorted_array_to_bst(nums):
    if not nums:
        return None
    mid = len(nums) // 2
    root = BSTNode(nums[mid])
    root.left = sorted_array_to_bst(nums[:mid])
    root.right = sorted_array_to_bst(nums[mid + 1:])
    return root

# Convert Sorted Linked List to BST
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def sorted_list_to_bst(head):
    arr = []
    while head:
        arr.append(head.val)
        head = head.next
    return sorted_array_to_bst(arr)
""",

    "twosuminbst": """
# Two Sum in BST - Inorder + Two Pointer
# Time Complexity: O(n)

def inorder_traversal(root, arr):
    if root:
        inorder_traversal(root.left, arr)
        arr.append(root.val)
        inorder_traversal(root.right, arr)

def two_sum_bst(root, target):
    arr = []
    inorder_traversal(root, arr)
    l, r = 0, len(arr) - 1
    while l < r:
        s = arr[l] + arr[r]
        if s == target:
            return True
        if s < target:
            l += 1
        else:
            r -= 1
    return False
""",

    "recoverbst": """
# Recover a Swapped BST - Inorder + Correction
# Time Complexity: O(n)

def recover_bst(root):
    first = second = prev = None

    def inorder(node):
        nonlocal first, second, prev
        if not node: return
        inorder(node.left)
        if prev and node.val < prev.val:
            if not first:
                first = prev
            second = node
        prev = node
        inorder(node.right)

    inorder(root)
    if first and second:
        first.val, second.val = second.val, first.val
""",

    "bstiterator": """
# BST Iterator - Inorder Traversal using Stack
# Time Complexity: O(1) avg per operation

class BSTIterator:
    def __init__(self, root):
        self.stack = []
        self._push_left(root)

    def _push_left(self, node):
        while node:
            self.stack.append(node)
            node = node.left

    def next(self):
        node = self.stack.pop()
        self._push_left(node.right)
        return node.val

    def has_next(self):
        return len(self.stack) > 0

# Example:
# it = BSTIterator(root)
# while it.has_next():
#     print(it.next())
""",

    "mergetwobsts": """
# Merge Two BSTs into a Sorted List
# Time Complexity: O(m + n)

def inorder_to_list(root, arr):
    if root:
        inorder_to_list(root.left, arr)
        arr.append(root.val)
        inorder_to_list(root.right, arr)

def merge_two_bsts(root1, root2):
    arr1, arr2 = [], []
    inorder_to_list(root1, arr1)
    inorder_to_list(root2, arr2)
    return sorted(arr1 + arr2)

# Example:
# merged = merge_two_bsts(root1, root2)
""",

    "predecessorsuccessor": """
# Inorder Predecessor & Successor in BST
# Time Complexity: O(h)

def find_predecessor_successor(root, key):
    predecessor = successor = None

    while root:
        if root.val == key:
            if root.left:
                temp = root.left
                while temp.right:
                    temp = temp.right
                predecessor = temp
            if root.right:
                temp = root.right
                while temp.left:
                    temp = temp.left
                successor = temp
            break
        elif key < root.val:
            successor = root
            root = root.left
        else:
            predecessor = root
            root = root.right
    return predecessor, successor

# Example:
# pred, succ = find_predecessor_successor(root, 15)
# print(pred.val if pred else None, succ.val if succ else None)
""",
    "heapify": """
# Heapify (Build Max-Heap) - Heap Sort Foundation
# Time Complexity: O(n)

def heapify(arr, n, i):
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2

    if l < n and arr[l] > arr[largest]:
        largest = l
    if r < n and arr[r] > arr[largest]:
        largest = r

    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)

def build_max_heap(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)

# Example:
# arr = [3, 5, 9, 6, 8, 20, 10, 12, 18, 9]
# build_max_heap(arr)
# print(arr)  # Max-Heap built
""",

    "heapinsertdelete": """
# Heap Insert & Delete - Min Heap Example
# Time Complexity: O(log n)

import heapq

# Insert element
def heap_insert(heap, val):
    heapq.heappush(heap, val)

# Delete min element
def heap_delete(heap):
    return heapq.heappop(heap) if heap else None

# Example:
# heap = []
# heap_insert(heap, 3)
# heap_insert(heap, 1)
# heap_insert(heap, 5)
# print(heap_delete(heap))  # Output: 1
""",

    "kthlargestorSmallest": """
# Kth Largest and Kth Smallest Element - Min/Max Heap
# Time Complexity: O(n log k)

import heapq

def kth_largest(nums, k):
    return heapq.nlargest(k, nums)[-1]

def kth_smallest(nums, k):
    return heapq.nsmallest(k, nums)[-1]

# Example:
# nums = [3, 2, 1, 5, 6, 4]
# print(kth_largest(nums, 2))   # Output: 5
# print(kth_smallest(nums, 2))  # Output: 2
""",

    "topkfrequent": """
# Top K Frequent Elements - Min Heap
# Time Complexity: O(n log k)

import heapq
from collections import Counter

def top_k_frequent(nums, k):
    freq = Counter(nums)
    return [num for num, _ in heapq.nlargest(k, freq.items(), key=lambda x: x[1])]

# Example:
# nums = [1,1,1,2,2,3]
# print(top_k_frequent(nums, 2))  # Output: [1, 2]
""",

    "medianofstream": """
# Median of Data Stream - Two Heaps (Max Heap + Min Heap)
# Time Complexity: O(log n)

import heapq

class MedianFinder:
    def __init__(self):
        self.small = []  # max-heap (store negatives)
        self.large = []  # min-heap

    def add_num(self, num):
        heapq.heappush(self.small, -num)
        heapq.heappush(self.large, -heapq.heappop(self.small))

        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self):
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2

# Example:
# mf = MedianFinder()
# mf.add_num(1)
# mf.add_num(2)
# print(mf.find_median())  # Output: 1.5
# mf.add_num(3)
# print(mf.find_median())  # Output: 2
""",

    "slidingwindowmedian": """
# Sliding Window Median - Two Heaps + Lazy Removal
# Time Complexity: O(n log k)

import heapq
from bisect import insort

def sliding_window_median(nums, k):
    window = sorted(nums[:k])
    medians = []
    for i in range(k, len(nums) + 1):
        if k % 2 == 1:
            medians.append(window[k // 2])
        else:
            medians.append((window[k // 2 - 1] + window[k // 2]) / 2)
        if i == len(nums): break
        window.remove(nums[i - k])
        insort(window, nums[i])
    return medians

# Example:
# nums = [1,3,-1,-3,5,3,6,7]
# k = 3
# print(sliding_window_median(nums, k))
# Output: [1, -1, -1, 3, 5, 6]
""",

    "reorganizestring": """
# Reorganize String - Max Heap (Greedy)
# Time Complexity: O(n log n)

import heapq
from collections import Counter

def reorganize_string(s):
    freq = Counter(s)
    max_heap = [(-cnt, ch) for ch, cnt in freq.items()]
    heapq.heapify(max_heap)

    prev_count, prev_char = 0, ''
    result = []

    while max_heap:
        count, char = heapq.heappop(max_heap)
        result.append(char)
        if prev_count < 0:
            heapq.heappush(max_heap, (prev_count, prev_char))
        count += 1
        prev_count, prev_char = count, char

    res_str = "".join(result)
    return res_str if len(res_str) == len(s) else ""

# Example:
# s = "aab"
# print(reorganize_string(s))  # Output: "aba"
""",

    "sortksortedarray": """
# Sort a K-Sorted Array - Min Heap
# Time Complexity: O(n log k)

import heapq

def sort_k_sorted_array(arr, k):
    heap = arr[:k + 1]
    heapq.heapify(heap)
    result = []

    for i in range(k + 1, len(arr)):
        result.append(heapq.heappop(heap))
        heapq.heappush(heap, arr[i])

    while heap:
        result.append(heapq.heappop(heap))

    return result

# Example:
# arr = [6, 5, 3, 2, 8, 10, 9]
# k = 3
# print(sort_k_sorted_array(arr, k))
# Output: [2, 3, 5, 6, 8, 9, 10]
""",
    "adjacencylistmatrix": """
# Graph Representation - Adjacency List & Matrix

# Adjacency List
def adjacency_list(n, edges):
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)  # for undirected
    return graph

# Adjacency Matrix
def adjacency_matrix(n, edges):
    matrix = [[0] * n for _ in range(n)]
    for u, v in edges:
        matrix[u][v] = 1
        matrix[v][u] = 1  # for undirected
    return matrix

# Example:
# edges = [(0, 1), (0, 2), (1, 2)]
# print(adjacency_list(3, edges))   # [[1,2],[0,2],[0,1]]
# print(adjacency_matrix(3, edges)) # [[0,1,1],[1,0,1],[1,1,0]]
""",

    "edgelist": """
# Edge List Representation

def edge_list(edges):
    return edges

# Example:
# edges = [(0, 1, 4), (0, 2, 1), (2, 1, 2)]
# print(edge_list(edges))  # [(0,1,4), (0,2,1), (2,1,2)]
""",

    "graphbfs": """
# BFS Traversal of a Graph - Iterative
# Time Complexity: O(V + E)

from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    result = []

    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
    return result

# Example:
# graph = {0: [1, 2], 1: [2], 2: [0, 3], 3: [3]}
# print(bfs(graph, 2))  # [2, 0, 3, 1]
""",

    "graphdfs": """
# DFS Traversal of a Graph - Recursive
# Time Complexity: O(V + E)

def dfs(graph, start, visited=None, result=None):
    if visited is None:
        visited = set()
    if result is None:
        result = []
    visited.add(start)
    result.append(start)
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited, result)
    return result

# Example:
# graph = {0: [1, 2], 1: [2], 2: [0, 3], 3: [3]}
# print(dfs(graph, 2))  # [2, 0, 1, 3]
""",

    "dijkstra": """
# Dijkstra's Algorithm - Shortest Path (Positive Weights)
# Time Complexity: O((V + E) log V)

import heapq

def dijkstra(graph, start):
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    pq = [(0, start)]

    while pq:
        current_dist, node = heapq.heappop(pq)
        if current_dist > dist[node]:
            continue
        for neighbor, weight in graph[node]:
            distance = current_dist + weight
            if distance < dist[neighbor]:
                dist[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    return dist

# Example:
# graph = {
#   0: [(1, 4), (2, 1)],
#   1: [(3, 1)],
#   2: [(1, 2), (3, 5)],
#   3: []
# }
# print(dijkstra(graph, 0))  # {0: 0, 1: 3, 2: 1, 3: 4}
""",

    "bellmanford": """
# Bellman-Ford Algorithm - Handles Negative Weights
# Time Complexity: O(V * E)

def bellman_ford(n, edges, src):
    dist = [float('inf')] * n
    dist[src] = 0

    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w

    # Check for negative weight cycle
    for u, v, w in edges:
        if dist[u] != float('inf') and dist[u] + w < dist[v]:
            return "Negative weight cycle detected!"
    return dist

# Example:
# edges = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1), (2, 3, 5)]
# print(bellman_ford(4, edges, 0))  # [0, 3, 1, 4]
""",

    "floydwarshall": """
# Floyd-Warshall Algorithm - All Pairs Shortest Path
# Time Complexity: O(V^3)

def floyd_warshall(graph):
    n = len(graph)
    dist = [[graph[i][j] for j in range(n)] for i in range(n)]

    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    return dist

# Example:
# INF = float('inf')
# graph = [
#   [0, 5, INF, 10],
#   [INF, 0, 3, INF],
#   [INF, INF, 0, 1],
#   [INF, INF, INF, 0]
# ]
# print(floyd_warshall(graph))
""",

    "astar": """
# A* Search Algorithm - Shortest Path with Heuristics
# Time Complexity: O(E log V)

import heapq

def a_star(graph, start, goal, h):
    open_set = [(0 + h[start], 0, start)]
    visited = set()

    while open_set:
        f, g, node = heapq.heappop(open_set)
        if node == goal:
            return g
        if node in visited:
            continue
        visited.add(node)

        for neighbor, cost in graph[node]:
            if neighbor not in visited:
                heapq.heappush(open_set, (g + cost + h[neighbor], g + cost, neighbor))
    return float('inf')

# Example:
# graph = {
#   'A': [('B', 1), ('C', 4)],
#   'B': [('C', 2), ('D', 5)],
#   'C': [('D', 1)],
#   'D': []
# }
# h = {'A': 7, 'B': 6, 'C': 2, 'D': 0}
# print(a_star(graph, 'A', 'D', h))  # Output: 4
""",

    "cycledetection": """
# Cycle Detection in Graph - Using DFS
# Time Complexity: O(V + E)

def has_cycle(graph):
    visited = set()
    rec_stack = set()

    def dfs(v):
        visited.add(v)
        rec_stack.add(v)
        for neighbor in graph[v]:
            if neighbor not in visited and dfs(neighbor):
                return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(v)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return True
    return False

# Example:
# graph = {0: [1], 1: [2], 2: [0]}
# print(has_cycle(graph))  # True
""",

    "topologicalsort": """
# Topological Sort - DFS Method
# Time Complexity: O(V + E)

def topological_sort(graph):
    visited = set()
    stack = []

    def dfs(v):
        visited.add(v)
        for neighbor in graph[v]:
            if neighbor not in visited:
                dfs(neighbor)
        stack.append(v)

    for node in graph:
        if node not in visited:
            dfs(node)

    return stack[::-1]

# Example:
# graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
# print(topological_sort(graph))  # One possible order: [4, 5, 2, 3, 1, 0]
""",

    "zeronebfs": """
# 0-1 BFS - Shortest Path in Graph with Edge Weights 0 or 1
# Time Complexity: O(V + E)

from collections import deque

def zero_one_bfs(graph, src):
    dist = {node: float('inf') for node in graph}
    dist[src] = 0
    dq = deque([src])

    while dq:
        node = dq.popleft()
        for neighbor, weight in graph[node]:
            if dist[node] + weight < dist[neighbor]:
                dist[neighbor] = dist[node] + weight
                if weight == 0:
                    dq.appendleft(neighbor)
                else:
                    dq.append(neighbor)
    return dist

# Example:
# graph = {
#   0: [(1, 0), (2, 1)],
#   1: [(2, 0)],
#   2: []
# }
# print(zero_one_bfs(graph, 0))  # {0: 0, 1: 0, 2: 0}
""",

    "prims": """
# Prim's Minimum Spanning Tree - Greedy
# Time Complexity: O(E log V)

import heapq

def prims(graph, start):
    visited = set()
    min_heap = [(0, start)]
    total_weight = 0

    while min_heap:
        weight, node = heapq.heappop(min_heap)
        if node in visited:
            continue
        visited.add(node)
        total_weight += weight

        for neighbor, w in graph[node]:
            if neighbor not in visited:
                heapq.heappush(min_heap, (w, neighbor))
    return total_weight

# Example:
# graph = {
#   0: [(1, 2), (3, 6)],
#   1: [(0, 2), (2, 3), (3, 8), (4, 5)],
#   2: [(1, 3), (4, 7)],
#   3: [(0, 6), (1, 8), (4, 9)],
#   4: [(1, 5), (2, 7), (3, 9)]
# }
# print(prims(graph, 0))  # Output: MST total weight
""",
    "kruskal": """
# Kruskal's Minimum Spanning Tree - Greedy + Union-Find
# Time Complexity: O(E log E)

class DSU:
    def __init__(self, n):
        self.parent = [i for i in range(n)]
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        xr, yr = self.find(x), self.find(y)
        if xr == yr:
            return False
        if self.rank[xr] < self.rank[yr]:
            self.parent[xr] = yr
        elif self.rank[xr] > self.rank[yr]:
            self.parent[yr] = xr
        else:
            self.parent[yr] = xr
            self.rank[xr] += 1
        return True

def kruskal(n, edges):
    dsu = DSU(n)
    edges.sort(key=lambda x: x[2])  # sort by weight
    mst_weight = 0
    mst_edges = []

    for u, v, w in edges:
        if dsu.union(u, v):
            mst_weight += w
            mst_edges.append((u, v, w))

    return mst_weight, mst_edges

# Example:
# edges = [(0, 1, 10), (0, 2, 6), (0, 3, 5), (1, 3, 15), (2, 3, 4)]
# print(kruskal(4, edges))
# Output: (19, [(2, 3, 4), (0, 3, 5), (0, 1, 10)])
""",

    "unionfind": """
# Union-Find (Disjoint Set Union - DSU)
# Time Complexity: O(alpha(n)) ~ O(1) amortized

class UnionFind:
    def __init__(self, n):
        self.parent = [i for i in range(n)]
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        xr, yr = self.find(x), self.find(y)
        if xr == yr:
            return False
        if self.rank[xr] < self.rank[yr]:
            self.parent[xr] = yr
        elif self.rank[xr] > self.rank[yr]:
            self.parent[yr] = xr
        else:
            self.parent[yr] = xr
            self.rank[xr] += 1
        return True

# Example:
# uf = UnionFind(5)
# uf.union(0, 1)
# uf.union(1, 2)
# print(uf.find(2))  # Output: 0
""",

    "kosaraju": """
# Kosaraju's Algorithm - Strongly Connected Components (SCC)
# Time Complexity: O(V + E)

from collections import defaultdict

def kosaraju_scc(graph, n):
    visited = [False] * n
    stack = []

    def dfs(v):
        visited[v] = True
        for nei in graph[v]:
            if not visited[nei]:
                dfs(nei)
        stack.append(v)

    # 1. Order vertices by finish time
    for i in range(n):
        if not visited[i]:
            dfs(i)

    # 2. Transpose the graph
    transpose = defaultdict(list)
    for u in range(n):
        for v in graph[u]:
            transpose[v].append(u)

    # 3. DFS in reverse order
    visited = [False] * n
    sccs = []

    def rev_dfs(v, component):
        visited[v] = True
        component.append(v)
        for nei in transpose[v]:
            if not visited[nei]:
                rev_dfs(nei, component)

    while stack:
        v = stack.pop()
        if not visited[v]:
            component = []
            rev_dfs(v, component)
            sccs.append(component)
    return sccs

# Example:
# graph = {0: [2, 3], 1: [0], 2: [1], 3: [4], 4: []}
# print(kosaraju_scc(graph, 5))  # Output: [[4], [3], [0, 2, 1]]
""",

    "tarjan": """
# Tarjan's Algorithm - Strongly Connected Components (SCC)
# Time Complexity: O(V + E)

def tarjans_scc(graph, n):
    index = [None] * n
    lowlink = [None] * n
    stack = []
    on_stack = [False] * n
    result = []
    current_index = [0]

    def dfs(v):
        index[v] = lowlink[v] = current_index[0]
        current_index[0] += 1
        stack.append(v)
        on_stack[v] = True

        for nei in graph[v]:
            if index[nei] is None:
                dfs(nei)
                lowlink[v] = min(lowlink[v], lowlink[nei])
            elif on_stack[nei]:
                lowlink[v] = min(lowlink[v], index[nei])

        if lowlink[v] == index[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == v:
                    break
            result.append(scc)

    for v in range(n):
        if index[v] is None:
            dfs(v)
    return result

# Example:
# graph = {0: [1], 1: [2], 2: [0], 1: [3], 3: []}
# print(tarjans_scc(graph, 4))  # Output: [[2, 1, 0], [3]]
""",

    "bridges": """
# Bridges in a Graph - Tarjan's Bridge-Finding Algorithm
# Time Complexity: O(V + E)

def find_bridges(n, edges):
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    ids = [-1] * n
    low = [0] * n
    bridges = []
    time = [0]

    def dfs(at, parent):
        ids[at] = low[at] = time[0]
        time[0] += 1
        for to in graph[at]:
            if to == parent: 
                continue
            if ids[to] == -1:
                dfs(to, at)
                low[at] = min(low[at], low[to])
                if ids[at] < low[to]:
                    bridges.append((at, to))
            else:
                low[at] = min(low[at], ids[to])

    for i in range(n):
        if ids[i] == -1:
            dfs(i, -1)

    return bridges

# Example:
# edges = [(0, 1), (1, 2), (2, 0), (1, 3)]
# print(find_bridges(4, edges))  # Output: [(1, 3)]
""",

    "eulerianpath": """
# Eulerian Path in Directed Graph - Hierholzer's Algorithm
# Time Complexity: O(V + E)

from collections import defaultdict

def eulerian_path(graph):
    indeg = defaultdict(int)
    outdeg = defaultdict(int)

    for u in graph:
        for v in graph[u]:
            outdeg[u] += 1
            indeg[v] += 1

    start = None
    for node in graph:
        if outdeg[node] - indeg[node] == 1:
            start = node
            break
    if not start:
        start = next(iter(graph))

    path = []

    def dfs(u):
        while graph[u]:
            v = graph[u].pop()
            dfs(v)
        path.append(u)

    dfs(start)
    return path[::-1]

# Example:
# graph = {0: [1], 1: [2], 2: [0]}
# print(eulerian_path(graph))  # Output: [0, 1, 2, 0]
""",

    "detectbipartite": """
# Detect Bipartite Graph - BFS Coloring
# Time Complexity: O(V + E)

from collections import deque

def is_bipartite(graph, n):
    color = [-1] * n
    for start in range(n):
        if color[start] == -1:
            queue = deque([start])
            color[start] = 0
            while queue:
                node = queue.popleft()
                for nei in graph[node]:
                    if color[nei] == -1:
                        color[nei] = 1 - color[node]
                        queue.append(nei)
                    elif color[nei] == color[node]:
                        return False
    return True

# Example:
# graph = [[1,3],[0,2],[1,3],[0,2]]
# print(is_bipartite(graph, 4))  # Output: True
""",
    "fibonacci": """
# Fibonacci - DP (Top-Down and Bottom-Up)
# Time Complexity: O(n)

# Bottom-Up DP
def fibonacci(n):
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]

# Example:
# print(fibonacci(10))  # Output: 55
""",

    "climbingstairs": """
# Climbing Stairs - DP
# Time Complexity: O(n)

def climbing_stairs(n):
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]

# Example:
# print(climbing_stairs(5))  # Output: 8
""",

    "houserobber": """
# House Robber - DP
# Time Complexity: O(n)

def house_robber(nums):
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    for i in range(2, len(nums)):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
    return dp[-1]

# Example:
# nums = [2,7,9,3,1]
# print(house_robber(nums))  # Output: 12
""",

    "jumpgame": """
# Jump Game - Greedy/DP
# Time Complexity: O(n)

def can_jump(nums):
    max_reach = 0
    for i, jump in enumerate(nums):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + jump)
    return True

# Example:
# nums = [2,3,1,1,4]
# print(can_jump(nums))  # Output: True
""",

    "maximumproductsubarray": """
# Maximum Product Subarray - DP
# Time Complexity: O(n)

def max_product_subarray(nums):
    max_prod = nums[0]
    min_prod = nums[0]
    result = nums[0]

    for i in range(1, len(nums)):
        if nums[i] < 0:
            max_prod, min_prod = min_prod, max_prod
        max_prod = max(nums[i], max_prod * nums[i])
        min_prod = min(nums[i], min_prod * nums[i])
        result = max(result, max_prod)
    return result

# Example:
# nums = [2,3,-2,4]
# print(max_product_subarray(nums))  # Output: 6
""",

    "uniquepaths": """
# Unique Paths in Grid - DP
# Time Complexity: O(m * n)

def unique_paths(m, n):
    dp = [[1] * n for _ in range(m)]
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
    return dp[m - 1][n - 1]

# Example:
# print(unique_paths(3, 7))  # Output: 28
""",

    "minimumpathsum": """
# Minimum Path Sum - DP
# Time Complexity: O(m * n)

def min_path_sum(grid):
    m, n = len(grid), len(grid[0])
    for i in range(1, m):
        grid[i][0] += grid[i - 1][0]
    for j in range(1, n):
        grid[0][j] += grid[0][j - 1]
    for i in range(1, m):
        for j in range(1, n):
            grid[i][j] += min(grid[i - 1][j], grid[i][j - 1])
    return grid[m - 1][n - 1]

# Example:
# grid = [[1,3,1],[1,5,1],[4,2,1]]
# print(min_path_sum(grid))  # Output: 7
""",

    "maximumsquare": """
# Maximum Square Sub-matrix - DP
# Time Complexity: O(m * n)

def maximal_square(matrix):
    if not matrix:
        return 0
    m, n = len(matrix), len(matrix[0])
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_side = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if matrix[i - 1][j - 1] == 1:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
                max_side = max(max_side, dp[i][j])
    return max_side * max_side

# Example:
# matrix = [[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]
# print(maximal_square(matrix))  # Output: 4
""",

    "cherrypickup": """
# Cherry Pickup - DP + DFS + Memoization
# Time Complexity: O(n^3)

from functools import lru_cache

def cherry_pickup(grid):
    n = len(grid)

    @lru_cache(None)
    def dp(r1, c1, r2):
        c2 = r1 + c1 - r2
        if (r1 >= n or c1 >= n or r2 >= n or c2 >= n or
            grid[r1][c1] == -1 or grid[r2][c2] == -1):
            return float('-inf')
        if r1 == c1 == n - 1:
            return grid[r1][c1]
        cherries = grid[r1][c1]
        if (r1, c1) != (r2, c2):
            cherries += grid[r2][c2]
        return cherries + max(
            dp(r1 + 1, c1, r2 + 1),
            dp(r1, c1 + 1, r2),
            dp(r1 + 1, c1, r2),
            dp(r1, c1 + 1, r2 + 1)
        )

    return max(0, dp(0, 0, 0))

# Example:
# grid = [[0,1,-1],[1,0,-1],[1,1,1]]
# print(cherry_pickup(grid))  # Output: 5
""",

    "dungeongame": """
# Dungeon Game - DP (Reverse traversal)
# Time Complexity: O(m * n)

def calculate_minimum_hp(dungeon):
    m, n = len(dungeon), len(dungeon[0])
    dp = [[0] * n for _ in range(m)]
    dp[-1][-1] = max(1, 1 - dungeon[-1][-1])

    for i in range(m - 2, -1, -1):
        dp[i][-1] = max(1, dp[i + 1][-1] - dungeon[i][-1])
    for j in range(n - 2, -1, -1):
        dp[-1][j] = max(1, dp[-1][j + 1] - dungeon[-1][j])

    for i in range(m - 2, -1, -1):
        for j in range(n - 2, -1, -1):
            dp[i][j] = max(1, min(dp[i + 1][j], dp[i][j + 1]) - dungeon[i][j])
    return dp[0][0]

# Example:
# dungeon = [[-2,-3,3],[-5,-10,1],[10,30,-5]]
# print(calculate_minimum_hp(dungeon))  # Output: 7
""",

    "lcs": """
# Longest Common Subsequence - DP
# Time Complexity: O(m * n)

def lcs(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]

# Example:
# print(lcs("abcde", "ace"))  # Output: 3
""",

    "lis": """
# Longest Increasing Subsequence - DP
# Time Complexity: O(n^2)

def lis(nums):
    n = len(nums)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if nums[i] > nums[j]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)

# Example:
# nums = [10,9,2,5,3,7,101,18]
# print(lis(nums))  # Output: 4
""",
    "lps": """
# Longest Palindromic Subsequence - DP
# Time Complexity: O(n^2)

def longest_palindromic_subsequence(s):
    n = len(s)
    dp = [[0] * n for _ in range(n)]

    for i in range(n):
        dp[i][i] = 1

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 + dp[i + 1][j - 1]
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]

# Example:
# print(longest_palindromic_subsequence("bbbab"))  # Output: 4
""",

    "editdistance": """
# Edit Distance (Levenshtein Distance) - DP
# Time Complexity: O(m * n)

def edit_distance(word1, word2):
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]

# Example:
# print(edit_distance("horse", "ros"))  # Output: 3
""",

    "wildcardmatching": """
# Wildcard Matching ('?' matches single, '*' matches sequence)
# Time Complexity: O(m * n)

def is_match(s, p):
    m, n = len(s), len(p)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True

    for j in range(1, n + 1):
        if p[j - 1] == '*':
            dp[0][j] = dp[0][j - 1]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j - 1] == '?' or p[j - 1] == s[i - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            elif p[j - 1] == '*':
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
    return dp[m][n]

# Example:
# print(is_match("adceb", "*a*b"))  # Output: True
""",

    "subsetSum": """
# Subset Sum - DP
# Time Complexity: O(n * sum)

def subset_sum(nums, target):
    n = len(nums)
    dp = [[False] * (target + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = True

    for i in range(1, n + 1):
        for j in range(1, target + 1):
            if nums[i - 1] <= j:
                dp[i][j] = dp[i - 1][j - nums[i - 1]] or dp[i - 1][j]
            else:
                dp[i][j] = dp[i - 1][j]
    return dp[n][target]

# Example:
# print(subset_sum([3, 34, 4, 12, 5, 2], 9))  # Output: True
""",

    "targetsum": """
# Target Sum - DP (Subset Sum Variant)
# Time Complexity: O(n * sum)

def target_sum(nums, target):
    total = sum(nums)
    if (total + target) % 2 != 0 or total < abs(target):
        return 0
    subset_target = (total + target) // 2
    dp = [0] * (subset_target + 1)
    dp[0] = 1

    for num in nums:
        for j in range(subset_target, num - 1, -1):
            dp[j] += dp[j - num]
    return dp[subset_target]

# Example:
# print(target_sum([1, 1, 1, 1, 1], 3))  # Output: 5
""",

    "palindromepartitioningii": """
# Palindrome Partitioning II - Min Cuts
# Time Complexity: O(n^2)

def min_cut(s):
    n = len(s)
    dp = [0] * n
    pal = [[False] * n for _ in range(n)]

    for i in range(n):
        min_cut_val = i
        for j in range(i + 1):
            if s[j] == s[i] and (i - j <= 1 or pal[j + 1][i - 1]):
                pal[j][i] = True
                min_cut_val = 0 if j == 0 else min(min_cut_val, dp[j - 1] + 1)
        dp[i] = min_cut_val
    return dp[-1]

# Example:
# print(min_cut("aab"))  # Output: 1
""",

    "knapsack01": """
# 0/1 Knapsack - DP
# Time Complexity: O(n * W)

def knapsack_01(weights, values, W):
    n = len(weights)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(1, W + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(values[i - 1] + dp[i - 1][w - weights[i - 1]], dp[i - 1][w])
            else:
                dp[i][w] = dp[i - 1][w]
    return dp[n][W]

# Example:
# weights = [1, 2, 3]
# values = [6, 10, 12]
# print(knapsack_01(weights, values, 5))  # Output: 22
""",

    "unboundedknapsack": """
# Unbounded Knapsack - DP
# Time Complexity: O(n * W)

def unbounded_knapsack(weights, values, W):
    dp = [0] * (W + 1)
    for i in range(len(weights)):
        for w in range(weights[i], W + 1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[W]

# Example:
# weights = [2, 3, 4, 5]
# values = [40, 50, 60, 70]
# print(unbounded_knapsack(weights, values, 8))  # Output: 160
""",

    "rodcutting": """
# Rod Cutting Problem - DP (Unbounded Knapsack)
# Time Complexity: O(n^2)

def rod_cutting(price, n):
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        for j in range(i):
            dp[i] = max(dp[i], price[j] + dp[i - j - 1])
    return dp[n]

# Example:
# price = [1,5,8,9,10,17,17,20]
# print(rod_cutting(price, 8))  # Output: 22
""",

    "coinchange": """
# Coin Change - Count Ways (Unbounded)
# Time Complexity: O(n * amount)

def coin_change(coins, amount):
    dp = [0] * (amount + 1)
    dp[0] = 1
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    return dp[amount]

# Example:
# coins = [1,2,5]
# print(coin_change(coins, 5))  # Output: 4
""",

    "houserobberiii": """
# House Robber III - Tree DP
# Time Complexity: O(n)

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def house_robber_iii(root):
    def dfs(node):
        if not node:
            return (0, 0)
        left = dfs(node.left)
        right = dfs(node.right)
        rob = node.val + left[1] + right[1]
        not_rob = max(left) + max(right)
        return (rob, not_rob)
    return max(dfs(root))

# Example:
# root = TreeNode(3)
# root.left = TreeNode(2)
# root.right = TreeNode(3)
# root.left.right = TreeNode(3)
# root.right.right = TreeNode(1)
# print(house_robber_iii(root))  # Output: 7
""",

    "tsp": """
# Travelling Salesman Problem (TSP) - DP + Bitmask
# Time Complexity: O(n^2 * 2^n)

from functools import lru_cache

def tsp_dp(graph):
    n = len(graph)

    @lru_cache(None)
    def visit(mask, pos):
        if mask == (1 << n) - 1:
            return graph[pos][0]
        ans = float('inf')
        for city in range(n):
            if mask & (1 << city) == 0:
                ans = min(ans, graph[pos][city] + visit(mask | (1 << city), city))
        return ans

    return visit(1, 0)

# Example:
# graph = [
#   [0, 10, 15, 20],
#   [10, 0, 35, 25],
#   [15, 35, 0, 30],
#   [20, 25, 30, 0]
# ]
# print(tsp_dp(graph))  # Output: 80
""",

    "assignmentproblem": """
# Assignment Problem - Hungarian Algorithm (O(n^3))

import math

def hungarian_algorithm(cost):
    from munkres import Munkres
    m = Munkres()
    indexes = m.compute(cost)
    total_cost = 0
    for row, col in indexes:
        total_cost += cost[row][col]
    return total_cost

# Example:
# cost = [
#   [9, 2, 7, 8],
#   [6, 4, 3, 7],
#   [5, 8, 1, 8],
#   [7, 6, 9, 4]
# ]
# print(hungarian_algorithm(cost))
# Output: 13
""",
    "trieinsertsearchdelete": """
# Trie (Prefix Tree) - Insert, Search, Delete, StartsWith
# Time Complexity: O(L) per operation (L = word length)

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def delete(self, word):
        def _delete(node, word, depth=0):
            if not node:
                return False
            if depth == len(word):
                if not node.is_end:
                    return False
                node.is_end = False
                return len(node.children) == 0
            char = word[depth]
            if char in node.children and _delete(node.children[char], word, depth + 1):
                del node.children[char]
                return not node.is_end and len(node.children) == 0
            return False
        _delete(self.root, word)

# Example:
# trie = Trie()
# trie.insert("apple")
# print(trie.search("apple"))  # True
# trie.delete("apple")
# print(trie.search("apple"))  # False
""",

    "wordsearchii": """
# Word Search II - Using Trie + DFS
# Time Complexity: O(m * n * 4^L)

class TrieNode2:
    def __init__(self):
        self.children = {}
        self.word = None

def find_words(board, words):
    root = TrieNode2()
    for w in words:
        node = root
        for ch in w:
            node = node.children.setdefault(ch, TrieNode2())
        node.word = w

    m, n = len(board), len(board[0])
    res = []

    def dfs(i, j, node):
        ch = board[i][j]
        if ch not in node.children:
            return
        node = node.children[ch]
        if node.word:
            res.append(node.word)
            node.word = None  # avoid duplicates
        board[i][j] = "#"
        for x, y in [(1,0),(-1,0),(0,1),(0,-1)]:
            if 0 <= i+x < m and 0 <= j+y < n:
                dfs(i+x, j+y, node)
        board[i][j] = ch

    for i in range(m):
        for j in range(n):
            dfs(i, j, root)
    return res

# Example:
# board = [
#   ["o","a","a","n"],
#   ["e","t","a","e"],
#   ["i","h","k","r"],
#   ["i","f","l","v"]
# ]
# words = ["oath","pea","eat","rain"]
# print(find_words(board, words))  # ['oath', 'eat']
""",

    "longestwordwithprefixes": """
# Longest Word with All Prefixes Present - Trie
# Time Complexity: O(N * L)

class TriePrefixNode:
    def __init__(self):
        self.children = {}
        self.end = False

def longest_word(words):
    root = TriePrefixNode()
    for word in words:
        node = root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TriePrefixNode()
            node = node.children[ch]
        node.end = True

    best = ""

    def dfs(node, path):
        nonlocal best
        if len(path) > len(best):
            best = path
        for ch, nxt in node.children.items():
            if nxt.end:
                dfs(nxt, path + ch)

    dfs(root, "")
    return best

# Example:
# words = ["w", "wo", "wor", "worl", "world"]
# print(longest_word(words))  # "world"
""",

    "replacewords": """
# Replace Words - Trie + Prefix Matching
# Time Complexity: O(N * L)

class ReplaceTrieNode:
    def __init__(self):
        self.children = {}
        self.word = None

def replace_words(dictionary, sentence):
    root = ReplaceTrieNode()
    for word in dictionary:
        node = root
        for ch in word:
            node = node.children.setdefault(ch, ReplaceTrieNode())
        node.word = word

    def replace(word):
        node = root
        for ch in word:
            if ch not in node.children:
                break
            node = node.children[ch]
            if node.word:
                return node.word
        return word

    return " ".join(replace(w) for w in sentence.split())

# Example:
# dictionary = ["cat","bat","rat"]
# sentence = "the cattle was rattled by the battery"
# print(replace_words(dictionary, sentence))
# Output: "the cat was rat by the bat"
""",

    "autocomplete": """
# Auto-complete System - Trie + DFS
# Time Complexity: O(L + K) for search (K = total suggestions)

class AutoTrieNode:
    def __init__(self):
        self.children = {}
        self.end = False

class AutoComplete:
    def __init__(self):
        self.root = AutoTrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, AutoTrieNode())
        node.end = True

    def suggestions(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        results = []

        def dfs(path, cur):
            if cur.end:
                results.append(path)
            for c, nxt in cur.children.items():
                dfs(path + c, nxt)

        dfs(prefix, node)
        return results

# Example:
# ac = AutoComplete()
# for w in ["apple", "app", "application", "apt", "banana"]:
#     ac.insert(w)
# print(ac.suggestions("app"))  # ['app', 'apple', 'application']
""",

    "maximumxorpair": """
# Maximum XOR Pair - Trie + Bit Manipulation
# Time Complexity: O(n * 32)

class XORNode:
    def __init__(self):
        self.children = {}

def find_maximum_xor(nums):
    root = XORNode()
    for num in nums:
        node = root
        for i in range(31, -1, -1):
            bit = (num >> i) & 1
            if bit not in node.children:
                node.children[bit] = XORNode()
            node = node.children[bit]

    max_xor = 0
    for num in nums:
        node = root
        curr_xor = 0
        for i in range(31, -1, -1):
            bit = (num >> i) & 1
            toggled_bit = 1 - bit
            if toggled_bit in node.children:
                curr_xor |= (1 << i)
                node = node.children[toggled_bit]
            else:
                node = node.children.get(bit, node)
        max_xor = max(max_xor, curr_xor)
    return max_xor

# Example:
# nums = [3, 10, 5, 25, 2, 8]
# print(find_maximum_xor(nums))  # Output: 28
""",

    "xortriequeries": """
# XOR Trie Queries - Query max XOR with given number
# Time Complexity: O(q * 32)

class XORTrieNode:
    def __init__(self):
        self.children = {}

class XORTrie:
    def __init__(self):
        self.root = XORTrieNode()

    def insert(self, num):
        node = self.root
        for i in range(31, -1, -1):
            bit = (num >> i) & 1
            if bit not in node.children:
                node.children[bit] = XORTrieNode()
            node = node.children[bit]

    def query(self, num):
        node = self.root
        max_xor = 0
        for i in range(31, -1, -1):
            bit = (num >> i) & 1
            toggled = 1 - bit
            if toggled in node.children:
                max_xor |= (1 << i)
                node = node.children[toggled]
            else:
                node = node.children.get(bit, node)
        return max_xor

# Example:
# trie = XORTrie()
# for num in [3, 10, 5, 25, 2, 8]:
#     trie.insert(num)
# print(trie.query(5))  # Output: 28
""",
    "rangesumquery": """
# Segment Tree - Range Sum Query
# Time Complexity: O(log n) for query & update

class SegmentTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        self.build(arr, 0, 0, self.n - 1)

    def build(self, arr, idx, l, r):
        if l == r:
            self.tree[idx] = arr[l]
            return
        mid = (l + r) // 2
        self.build(arr, 2 * idx + 1, l, mid)
        self.build(arr, 2 * idx + 2, mid + 1, r)
        self.tree[idx] = self.tree[2 * idx + 1] + self.tree[2 * idx + 2]

    def query(self, idx, l, r, ql, qr):
        if qr < l or ql > r:
            return 0
        if ql <= l and r <= qr:
            return self.tree[idx]
        mid = (l + r) // 2
        left = self.query(2 * idx + 1, l, mid, ql, qr)
        right = self.query(2 * idx + 2, mid + 1, r, ql, qr)
        return left + right

    def update(self, idx, l, r, pos, val):
        if l == r:
            self.tree[idx] = val
            return
        mid = (l + r) // 2
        if pos <= mid:
            self.update(2 * idx + 1, l, mid, pos, val)
        else:
            self.update(2 * idx + 2, mid + 1, r, pos, val)
        self.tree[idx] = self.tree[2 * idx + 1] + self.tree[2 * idx + 2]

# Example:
# arr = [1, 3, 5, 7, 9, 11]
# seg = SegmentTree(arr)
# print(seg.query(0, 0, seg.n - 1, 1, 3))  # Output: 15
# seg.update(0, 0, seg.n - 1, 1, 10)
# print(seg.query(0, 0, seg.n - 1, 1, 3))  # Output: 22
""",

    "minmaxquery": """
# Segment Tree - Range Min and Max Query
# Time Complexity: O(log n)

class MinMaxSegmentTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.min_tree = [float('inf')] * (4 * self.n)
        self.max_tree = [float('-inf')] * (4 * self.n)
        self.build(arr, 0, 0, self.n - 1)

    def build(self, arr, idx, l, r):
        if l == r:
            self.min_tree[idx] = arr[l]
            self.max_tree[idx] = arr[l]
            return
        mid = (l + r) // 2
        self.build(arr, 2 * idx + 1, l, mid)
        self.build(arr, 2 * idx + 2, mid + 1, r)
        self.min_tree[idx] = min(self.min_tree[2 * idx + 1], self.min_tree[2 * idx + 2])
        self.max_tree[idx] = max(self.max_tree[2 * idx + 1], self.max_tree[2 * idx + 2])

    def range_min(self, idx, l, r, ql, qr):
        if qr < l or ql > r:
            return float('inf')
        if ql <= l and r <= qr:
            return self.min_tree[idx]
        mid = (l + r) // 2
        return min(self.range_min(2 * idx + 1, l, mid, ql, qr),
                   self.range_min(2 * idx + 2, mid + 1, r, ql, qr))

    def range_max(self, idx, l, r, ql, qr):
        if qr < l or ql > r:
            return float('-inf')
        if ql <= l and r <= qr:
            return self.max_tree[idx]
        mid = (l + r) // 2
        return max(self.range_max(2 * idx + 1, l, mid, ql, qr),
                   self.range_max(2 * idx + 2, mid + 1, r, ql, qr))

# Example:
# arr = [2, 5, 1, 4, 9, 3]
# tree = MinMaxSegmentTree(arr)
# print(tree.range_min(0, 0, tree.n - 1, 1, 4))  # Output: 1
# print(tree.range_max(0, 0, tree.n - 1, 1, 4))  # Output: 9
""",

    "lazypropagation": """
# Segment Tree with Lazy Propagation - Range Update
# Time Complexity: O(log n)

class LazySegmentTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        self.lazy = [0] * (4 * self.n)
        self.build(arr, 0, 0, self.n - 1)

    def build(self, arr, idx, l, r):
        if l == r:
            self.tree[idx] = arr[l]
            return
        mid = (l + r) // 2
        self.build(arr, 2 * idx + 1, l, mid)
        self.build(arr, 2 * idx + 2, mid + 1, r)
        self.tree[idx] = self.tree[2 * idx + 1] + self.tree[2 * idx + 2]

    def update_range(self, idx, l, r, ql, qr, val):
        if self.lazy[idx] != 0:
            self.tree[idx] += (r - l + 1) * self.lazy[idx]
            if l != r:
                self.lazy[2 * idx + 1] += self.lazy[idx]
                self.lazy[2 * idx + 2] += self.lazy[idx]
            self.lazy[idx] = 0

        if qr < l or ql > r:
            return

        if ql <= l and r <= qr:
            self.tree[idx] += (r - l + 1) * val
            if l != r:
                self.lazy[2 * idx + 1] += val
                self.lazy[2 * idx + 2] += val
            return

        mid = (l + r) // 2
        self.update_range(2 * idx + 1, l, mid, ql, qr, val)
        self.update_range(2 * idx + 2, mid + 1, r, ql, qr, val)
        self.tree[idx] = self.tree[2 * idx + 1] + self.tree[2 * idx + 2]

    def query(self, idx, l, r, ql, qr):
        if self.lazy[idx] != 0:
            self.tree[idx] += (r - l + 1) * self.lazy[idx]
            if l != r:
                self.lazy[2 * idx + 1] += self.lazy[idx]
                self.lazy[2 * idx + 2] += self.lazy[idx]
            self.lazy[idx] = 0

        if qr < l or ql > r:
            return 0

        if ql <= l and r <= qr:
            return self.tree[idx]

        mid = (l + r) // 2
        return self.query(2 * idx + 1, l, mid, ql, qr) + self.query(2 * idx + 2, mid + 1, r, ql, qr)

# Example:
# arr = [1, 3, 5, 7, 9, 11]
# seg = LazySegmentTree(arr)
# seg.update_range(0, 0, seg.n - 1, 1, 3, 10)
# print(seg.query(0, 0, seg.n - 1, 1, 3))  # Output: 55
""",

    "pointupdate": """
# Fenwick Tree (BIT) - Point Update + Range Query
# Time Complexity: O(log n)

class FenwickTree:
    def __init__(self, n):
        self.bit = [0] * (n + 1)
        self.n = n

    def update(self, idx, delta):
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & -idx

    def query(self, idx):
        res = 0
        while idx > 0:
            res += self.bit[idx]
            idx -= idx & -idx
        return res

    def range_query(self, l, r):
        return self.query(r) - self.query(l - 1)

# Example:
# bit = FenwickTree(6)
# arr = [1, 3, 5, 7, 9, 11]
# for i, val in enumerate(arr, 1):
#     bit.update(i, val)
# print(bit.range_query(2, 4))  # Output: 15
""",

    "inversioncount": """
# Inversion Count - Merge Sort Technique
# Time Complexity: O(n log n)

def count_inversions(arr):
    def merge_sort(nums):
        if len(nums) <= 1:
            return nums, 0
        mid = len(nums) // 2
        left, inv_left = merge_sort(nums[:mid])
        right, inv_right = merge_sort(nums[mid:])
        merged, inv_split = merge(left, right)
        return merged, inv_left + inv_right + inv_split

    def merge(left, right):
        merged = []
        i = j = inv_count = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                inv_count += len(left) - i
                j += 1
        merged += left[i:]
        merged += right[j:]
        return merged, inv_count

    _, inv_count = merge_sort(arr)
    return inv_count

# Example:
# arr = [2, 4, 1, 3, 5]
# print(count_inversions(arr))  # Output: 3
""",

    "2dbit": """
# 2D BIT (Fenwick Tree) - Range Sum Query in 2D
# Time Complexity: O(log m * log n)

class BIT2D:
    def __init__(self, m, n):
        self.m, self.n = m, n
        self.bit = [[0] * (n + 1) for _ in range(m + 1)]

    def update(self, x, y, delta):
        i = x + 1
        while i <= self.m:
            j = y + 1
            while j <= self.n:
                self.bit[i][j] += delta
                j += j & -j
            i += i & -i

    def query(self, x, y):
        res = 0
        i = x + 1
        while i > 0:
            j = y + 1
            while j > 0:
                res += self.bit[i][j]
                j -= j & -j
            i -= i & -i
        return res

    def range_query(self, x1, y1, x2, y2):
        return (self.query(x2, y2) - self.query(x1 - 1, y2)
                - self.query(x2, y1 - 1) + self.query(x1 - 1, y1 - 1))

# Example:
# bit2d = BIT2D(4, 4)
# bit2d.update(1, 1, 5)
# bit2d.update(2, 3, 7)
# print(bit2d.range_query(1, 1, 2, 3))  # Output: 12
""",
    "setbits": """
# Count Set Bits (Brian Kernighan's Algorithm)
# Time Complexity: O(log n)

def count_set_bits(n):
    count = 0
    while n:
        n &= (n - 1)
        count += 1
    return count

# Example:
# print(count_set_bits(29))  # 29 = 11101 -> Output: 4
""",

    "poweroftwo": """
# Check if a number is Power of Two
# Time Complexity: O(1)

def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

# Example:
# print(is_power_of_two(16))  # True
# print(is_power_of_two(18))  # False
""",

    "xor": """
# XOR Basics - Properties and Tricks
# a ^ a = 0
# a ^ 0 = a
# a ^ b ^ a = b

def xor_two_numbers(a, b):
    return a ^ b

# Example:
# print(xor_two_numbers(5, 7))  # Output: 2 (101 ^ 111 = 010)
""",

    "missingnumber": """
# Missing Number in [0, n] - XOR Method
# Time Complexity: O(n)

def missing_number(nums):
    res = len(nums)
    for i, num in enumerate(nums):
        res ^= i ^ num
    return res

# Example:
# nums = [3, 0, 1]
# print(missing_number(nums))  # Output: 2
""",

    "duplicatenumber": """
# Find Duplicate Number - XOR or Floyd’s Cycle Detection
# Time Complexity: O(n)

def find_duplicate(nums):
    slow = nums[0]
    fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    fast = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow

# Example:
# nums = [1, 3, 4, 2, 2]
# print(find_duplicate(nums))  # Output: 2
""",

    "singlenumber": """
# Find Single Number - XOR Method
# Time Complexity: O(n)

def single_number(nums):
    res = 0
    for num in nums:
        res ^= num
    return res

# Example:
# nums = [4,1,2,1,2]
# print(single_number(nums))  # Output: 4
""",

    "bitmasksubsets": """
# Generate All Subsets Using Bitmask
# Time Complexity: O(2^n)

def bitmask_subsets(nums):
    n = len(nums)
    result = []
    for mask in range(1 << n):
        subset = [nums[i] for i in range(n) if mask & (1 << i)]
        result.append(subset)
    return result

# Example:
# nums = [1, 2, 3]
# print(bitmask_subsets(nums))
# Output: [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]
""",

    "sumofxors": """
# Sum of XOR of All Subsets - Bit Contribution
# Time Complexity: O(n)

def sum_of_xors(nums):
    n = len(nums)
    total_xor = 0
    for bit in range(32):
        set_count = sum((num >> bit) & 1 for num in nums)
        total_xor += (set_count * (1 << bit) * (1 << (n - 1)))
    return total_xor

# Example:
# nums = [1, 3]
# print(sum_of_xors(nums))  # Output: 6
""",

    "swaptogglebits": """
# Swap and Toggle Specific Bits
# Time Complexity: O(1)

def swap_bits(n, i, j):
    # Swap bits at positions i and j
    if ((n >> i) & 1) != ((n >> j) & 1):
        n ^= (1 << i) | (1 << j)
    return n

def toggle_bit(n, i):
    # Toggle bit at position i
    return n ^ (1 << i)

# Example:
# print(bin(swap_bits(0b10110, 1, 3)))   # Swap bit 1 and 3
# print(bin(toggle_bit(0b10110, 2)))     # Toggle bit 2
""",
    "gcdlcm": """
# GCD (Euclidean Algorithm) and LCM
# Time Complexity: O(log min(a, b))

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return abs(a * b) // gcd(a, b)

# Example:
# print(gcd(54, 24))  # Output: 6
# print(lcm(4, 6))    # Output: 12
""",

    "sieveoferatosthenes": """
# Sieve of Eratosthenes - Generate all primes <= n
# Time Complexity: O(n log log n)

def sieve_of_eratosthenes(n):
    primes = [True] * (n + 1)
    primes[0] = primes[1] = False
    p = 2
    while p * p <= n:
        if primes[p]:
            for i in range(p * p, n + 1, p):
                primes[i] = False
        p += 1
    return [i for i, is_prime in enumerate(primes) if is_prime]

# Example:
# print(sieve_of_eratosthenes(30))
# Output: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
""",

    "primefactorization": """
# Prime Factorization - Trial Division
# Time Complexity: O(sqrt(n))

def prime_factorization(n):
    factors = []
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    f = 3
    while f * f <= n:
        while n % f == 0:
            factors.append(f)
            n //= f
        f += 2
    if n > 1:
        factors.append(n)
    return factors

# Example:
# print(prime_factorization(84))  # Output: [2, 2, 3, 7]
""",

    "modularexponentiation": """
# Modular Exponentiation (a^b % m)
# Time Complexity: O(log b)

def mod_pow(a, b, m):
    result = 1
    a %= m
    while b > 0:
        if b & 1:
            result = (result * a) % m
        a = (a * a) % m
        b >>= 1
    return result

# Example:
# print(mod_pow(2, 10, 1000))  # Output: 24
""",

    "modularinverse": """
# Modular Inverse using Extended Euclidean Algorithm
# Time Complexity: O(log m)

def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1

def mod_inverse(a, m):
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        return None  # Inverse doesn't exist
    return x % m

# Example:
# print(mod_inverse(3, 11))  # Output: 4 (since 3*4 % 11 = 1)
""",

    "fastpower": """
# Fast Exponentiation - Binary Exponentiation
# Time Complexity: O(log n)

def fast_power(a, b):
    result = 1
    while b > 0:
        if b & 1:
            result *= a
        a *= a
        b >>= 1
    return result

# Example:
# print(fast_power(2, 10))  # Output: 1024
""",

    "ncrpascal": """
# nCr (Combinations) using Pascal's Triangle
# Time Complexity: O(n^2)

def generate_pascals_triangle(n):
    C = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        C[i][0] = C[i][i] = 1
        for j in range(1, i):
            C[i][j] = C[i - 1][j - 1] + C[i - 1][j]
    return C

def nCr(n, r):
    C = generate_pascals_triangle(n)
    return C[n][r]

# Example:
# print(nCr(5, 2))  # Output: 10
""",

    "matrixexponentiation": """
# Matrix Exponentiation - Fast Fibonacci or Linear Recurrence
# Time Complexity: O(log n)

def mat_mult(A, B):
    n = len(A)
    C = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C

def mat_pow(A, n):
    size = len(A)
    result = [[1 if i == j else 0 for j in range(size)] for i in range(size)]
    while n > 0:
        if n & 1:
            result = mat_mult(result, A)
        A = mat_mult(A, A)
        n >>= 1
    return result

# Example: Fibonacci using matrix exponentiation
def fib_matrix(n):
    if n == 0:
        return 0
    F = [[1, 1], [1, 0]]
    result = mat_pow(F, n - 1)
    return result[0][0]

# Example:
# print(fib_matrix(10))  # Output: 55
""",

    "trailingzeros": """
# Count Trailing Zeros in Factorial n!
# Time Complexity: O(log n)

def trailing_zeros(n):
    count = 0
    i = 5
    while n // i:
        count += n // i
        i *= 5
    return count

# Example:
# print(trailing_zeros(100))  # Output: 24
""",

    "armstrongnumber": """
# Check Armstrong Number
# Time Complexity: O(d) where d = number of digits

def is_armstrong(n):
    digits = list(map(int, str(n)))
    power = len(digits)
    return sum(d ** power for d in digits) == n

# Example:
# print(is_armstrong(153))  # Output: True
""",

    "perfectnumber": """
# Check Perfect Number (Sum of Proper Divisors = n)
# Time Complexity: O(sqrt(n))

def is_perfect_number(n):
    if n <= 1:
        return False
    s = 1
    i = 2
    while i * i <= n:
        if n % i == 0:
            s += i
            if i != n // i:
                s += n // i
        i += 1
    return s == n

# Example:
# print(is_perfect_number(28))  # Output: True
""",
    "reservoirsampling": """
# Reservoir Sampling - Random k elements from stream of unknown size
# Time Complexity: O(n)

import random

def reservoir_sampling(stream, k):
    reservoir = stream[:k]
    for i in range(k, len(stream)):
        j = random.randint(0, i)
        if j < k:
            reservoir[j] = stream[i]
    return reservoir

# Example:
# stream = [1, 2, 3, 4, 5, 6, 7, 8]
# print(reservoir_sampling(stream, 3))
""",

    "kmpalgorithm": """
# KMP (Knuth-Morris-Pratt) - String Pattern Matching
# Time Complexity: O(n + m)

def kmp_search(text, pattern):
    n, m = len(text), len(pattern)
    lps = [0] * m

    # Precompute LPS array
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = lps[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
            lps[i] = j

    # Search
    res = []
    j = 0
    for i in range(n):
        while j > 0 and text[i] != pattern[j]:
            j = lps[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            res.append(i - m + 1)
            j = lps[j - 1]
    return res

# Example:
# print(kmp_search("ababcabcabababd", "ababd"))  # Output: [10]
""",

    "rabinkarp": """
# Rabin-Karp - String Matching Using Rolling Hash
# Time Complexity: O(n + m)

def rabin_karp(text, pattern, d=256, q=101):
    n, m = len(text), len(pattern)
    p = t = 0
    h = pow(d, m - 1, q)
    res = []

    # Precompute hash
    for i in range(m):
        p = (d * p + ord(pattern[i])) % q
        t = (d * t + ord(text[i])) % q

    for i in range(n - m + 1):
        if p == t and text[i:i + m] == pattern:
            res.append(i)
        if i < n - m:
            t = (d * (t - ord(text[i]) * h) + ord(text[i + m])) % q
            if t < 0:
                t += q
    return res

# Example:
# print(rabin_karp("ababcabcabababd", "ababd"))  # Output: [10]
""",

    "zalgorithm": """
# Z-Algorithm - Pattern Search / String Matching
# Time Complexity: O(n + m)

def z_algorithm(s):
    n = len(s)
    Z = [0] * n
    l = r = 0
    for i in range(1, n):
        if i <= r:
            Z[i] = min(r - i + 1, Z[i - l])
        while i + Z[i] < n and s[Z[i]] == s[i + Z[i]]:
            Z[i] += 1
        if i + Z[i] - 1 > r:
            l, r = i, i + Z[i] - 1
    return Z

def z_search(text, pattern):
    concat = pattern + "$" + text
    Z = z_algorithm(concat)
    m = len(pattern)
    return [i - m - 1 for i in range(len(Z)) if Z[i] == m]

# Example:
# print(z_search("ababcabcabababd", "ababd"))  # Output: [10]
""",

    "manacher": """
# Manacher's Algorithm - Longest Palindromic Substring
# Time Complexity: O(n)

def manacher(s):
    s = "#" + "#".join(s) + "#"
    n = len(s)
    P = [0] * n
    C = R = 0
    for i in range(n):
        mirror = 2 * C - i
        if i < R:
            P[i] = min(R - i, P[mirror])
        while i - P[i] - 1 >= 0 and i + P[i] + 1 < n and s[i + P[i] + 1] == s[i - P[i] - 1]:
            P[i] += 1
        if i + P[i] > R:
            C, R = i, i + P[i]
    max_len, center = max((P[i], i) for i in range(n))
    start = (center - max_len) // 2
    return s[center - max_len + 1:center + max_len:2]

# Example:
# print(manacher("babad"))  # Output: "bab" or "aba"
""",

    "unionfindrollback": """
# Union-Find Rollback - Supports Undo Operations
# Time Complexity: ~O(α(n)) per op

class UnionFindRollback:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.history = []

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            self.history.append((-1, -1, -1, -1))
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.history.append((a, b, self.parent[b], self.size[a]))
        self.parent[b] = a
        self.size[a] += self.size[b]
        return True

    def rollback(self):
        a, b, old_parent, old_size = self.history.pop()
        if a == -1:
            return
        self.parent[b] = old_parent
        self.size[a] = old_size

# Example:
# uf = UnionFindRollback(5)
# uf.union(0, 1)
# uf.union(1, 2)
# uf.rollback()
""",

    "mosalgorithm": """
# Mo's Algorithm - Offline Range Queries (sqrt decomposition)
# Time Complexity: O((N + Q) * sqrt(N))

import math

def mos_algorithm(arr, queries):
    block_size = int(math.sqrt(len(arr)))
    queries.sort(key=lambda x: (x[0] // block_size, x[1]))

    freq = {}
    curr_ans = 0
    ans = [0] * len(queries)

    def add(x):
        nonlocal curr_ans
        freq[x] = freq.get(x, 0) + 1
        if freq[x] == 1:
            curr_ans += 1

    def remove(x):
        nonlocal curr_ans
        freq[x] -= 1
        if freq[x] == 0:
            curr_ans -= 1

    L = R = 0
    for i, (l, r) in enumerate(queries):
        while L > l:
            L -= 1
            add(arr[L])
        while R <= r:
            add(arr[R])
            R += 1
        while L < l:
            remove(arr[L])
            L += 1
        while R > r + 1:
            R -= 1
            remove(arr[R])
        ans[i] = curr_ans
    return ans

# Example:
# arr = [1, 1, 2, 1, 3]
# queries = [(0, 4), (1, 3), (2, 4)]
# print(mos_algorithm(arr, queries))  # Output: [3, 2, 3]
""",

    "centroiddecomposition": """
# Centroid Decomposition - Divide & Conquer on Trees
# Time Complexity: O(n log n)

from collections import defaultdict

def centroid_decomposition(n, tree):
    size = [0] * n
    visited = [False] * n
    centroid_tree = defaultdict(list)

    def dfs_size(u, p):
        size[u] = 1
        for v in tree[u]:
            if v != p and not visited[v]:
                size[u] += dfs_size(v, u)
        return size[u]

    def find_centroid(u, p, n):
        for v in tree[u]:
            if v != p and not visited[v] and size[v] > n // 2:
                return find_centroid(v, u, n)
        return u

    def decompose(u, p):
        n_size = dfs_size(u, -1)
        centroid = find_centroid(u, -1, n_size)
        visited[centroid] = True
        if p != -1:
            centroid_tree[p].append(centroid)
            centroid_tree[centroid].append(p)
        for v in tree[centroid]:
            if not visited[v]:
                decompose(v, centroid)
        return centroid

    root = decompose(0, -1)
    return centroid_tree, root

# Example:
# tree = {0:[1,2], 1:[0,3,4], 2:[0], 3:[1], 4:[1]}
# print(centroid_decomposition(5, tree))
""",

    "convexhull": """
# Convex Hull - Graham Scan / Monotonic Chain
# Time Complexity: O(n log n)

def convex_hull(points):
    points = sorted(points)
    if len(points) <= 1:
        return points

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]

# Example:
# points = [(0,0),(1,1),(2,2),(2,0),(2,4),(3,3)]
# print(convex_hull(points))  # Convex hull points
""",

}

# ------------------------------
# 🧠 CORE FUNCTIONS
# ------------------------------

# ===========================================
# 📁 CATEGORY - ALGORITHM MAPPING
# ===========================================

categories = {
    "Arrays And Strings": [
        "two_sum", "linearsearch", "binarysearch", "ternarysearch",
        "bubblesort", "selectionsort", "insertionsort", "mergesort",
        "quicksort", "countingsort", "radixsort", "bucketsort",
        "maxsumsubarrayofsizek", "longestsubstringwithkdistinct",
        "prefixsumarray", "differencearray", "kadane",
        "spiralmatrix", "rotatematrix", "jumpgame",
        "minimumplatforms", "naivepatternsearch", "kmpalgorithm",
        "rabinkarp", "zalgorithm"
    ],

    "Linked Lists": [
        "singlylinkedlist", "doublylinkedlist", "circularlinkedlist",
        "reverselinkedlist", "detectandremoveloop", "mergetwosortedlists",
        "addtwonumbers", "copylistwithrandompointer", "lrucache",
        "intersectionoftwolls", "sortllusingmergesort"
    ],

    "Stack And Queue": [
        "implementstack", "stackusingtwoqueues", "queueusingtwostacks",
        "balancedparentheses", "nextgreaterelement", "dailytemperatures",
        "minstack", "infixtopostfix", "evaluatepostfix",
        "monotonicstack", "slidingwindowmaximum"
    ],

    "Recursion And Backtracking": [
        "towerofhanoi", "subsets", "permutations", "combinationsum",
        "palindromepartitioning", "wordsearch", "nqueens",
        "sudokusolver", "generateparentheses", "ratinamaze",
        "lettercombinationsofphonenumber"
    ],

    "Binary Trees": [
        "treetraversals", "views", "heightdepth", "diameterofbinarytree",
        "balancedtree", "mirrortree", "buildtree", "serializedeserialize",
        "boundarytraversal", "burntree", "lca", "flattenbinarytree",
        "verticalordertraversal"
    ],

    "Binary Search Trees (BST)": [
        "bstsearchinsertdelete", "validatebst", "kthsmallestlargest",
        "lcainbst", "converttobst", "twosuminbst", "recoverbst",
        "bstiterator", "mergetwobsts", "predecessorsuccessor"
    ],

    "Heap / Priority Queue": [
        "heapify", "insertdelete", "kthlargestorsmallest", "topkfrequent",
        "medianofstream", "slidingwindowmedian", "reorganizestring",
        "sortksortedarray"
    ],

    "Graphs": [
        "adjacencylistmatrix", "edgelist", "graphbfs", "graphdfs",
        "dijkstra", "bellmanford", "floydwarshall", "astar",
        "cycledetection", "topologicalsort", "zeronebfs",
        "prims", "kruskal", "unionfind", "kosaraju",
        "tarjan", "bridges", "eulerianpath", "detectbipartite"
    ],

    "Dynamic Programming": [
        "fibonacci", "climbingstairs", "houserobber", "jumpgame",
        "maximumproductsubarray", "uniquepaths", "minimumpathsum",
        "maximumsquare", "cherrypickup", "dungeongame", "lcs",
        "lis", "lps", "editdistance", "wildcardmatching",
        "subsetsum", "targetsum", "palindromepartitioningii",
        "knapsack01", "unboundedknapsack", "rodcutting",
        "coinchange", "houserobberiii", "tsp", "assignmentproblem"
    ],

    "Trie": [
        "trieinsertsearchdelete", "wordsearchii", "longestwordwithprefixes",
        "replacewords", "autocomplete", "maximumxorpair", "xortriequeries"
    ],

    "Segment Tree And BIT": [
        "rangesumquery", "minmaxquery", "lazypropagation",
        "pointupdate", "inversioncount", "2dbit"
    ],

    "Bit Manipulation": [
        "setbits", "poweroftwo", "xor", "missingnumber",
        "duplicatenumber", "singlenumber", "bitmasksubsets",
        "sumofxors", "swaptogglebits"
    ],

    "Math And Number Theory": [
        "gcdlcm", "sieveoferatosthenes", "primefactorization",
        "modularexponentiation", "modularinverse", "fastpower",
        "ncrpascal", "matrixexponentiation", "trailingzeros",
        "armstrongnumber", "perfectnumber"
    ],

    "Miscellaneous": [
        "reservoirsampling", "kmpalgorithm", "rabinkarp", "zalgorithm",
        "manacher", "unionfindrollback", "mosalgorithm",
        "centroiddecomposition", "convexhull"
    ]
}


# ===========================================
# 📜 REPLACEMENT SHOW FUNCTION
# ===========================================

def show(name: str) -> str:
    name = name.strip().lower().replace(" ", "").replace("-", "").replace("_", "")

    # 1️⃣ Show all categories
    if name in ["category", "categories", "list"]:
        return "\n".join(categories.keys())

    # 2️⃣ Show all algorithms in a category
    for cat, algos in categories.items():
        if name == cat.lower().replace(" ", "").replace("&", "").replace("-", ""):
            return "\n".join(algos)

    # 3️⃣ Try exact match
    if name in algorithms:
        return algorithms[name]

    # 4️⃣ Try partial match
    for key in algorithms:
        if name in key.replace("_", "").replace("-", "").replace(" ", ""):
            return algorithms[key]

    return "❌ Not found. Use show('category') to see all categories."


