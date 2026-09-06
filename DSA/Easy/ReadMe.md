# Problem 1: Balanced Brackets

### Approach & Logic
* Pretty familiar with this pattern since I had already solved "Valid Parentheses" on LeetCode, so the core logic was straightforward.
* **Algorithm:**
  * Traverse the string and push any opening bracket (`(`, `{`, `[`) straight onto a stack.
  * As soon as a closing bracket appears, check if the stack's top matches the corresponding opening pair.
  * If it matches, pop it off and continue. If the stack is empty or the top doesn't match, return `NO` immediately.
  * If the stack is empty at the very end, all brackets were valid and balanced (`YES`).

> **Takeaway:** Coming from LeetCode where inputs are already fed into functions, handling raw CLI standard input (`cin`) through the terminal stream was a solid refresher on how input buffers actually behave.
> https://leetcode.com/u/anantchaturvedi/

### Output & Verification
<img width="1470" height="956" alt="Screenshot 2026-09-05 at 11 36 07 PM" src="https://github.com/user-attachments/assets/254c38a7-25a1-4ef7-81f2-77934ab9247a" />

---

# Problem 2: Second Largest Distinct Element

### Approach & Logic
* Kept it optimal with a single-pass $O(N)$ check instead of sorting the whole array.
* **Algorithm:**
  * Maintain two variables: `max1` (largest) and `max2` (second largest).
  * If the incoming number is strictly greater than `max1`, bump `max1` down to `max2`, and set `max1` to the new value.
  * If it's smaller than `max1` but strictly larger than `max2`, update `max2` (this neatly ignores duplicates of `max1`).
* **Edge Cases Handled:**
  * Constraints allowed numbers down to $-10^9$, so initializing with `0` would fail on negative arrays. Both variables are pre-assigned to `LLONG_MIN` to ensure any valid number triggers the swap.
  * If `max2` remains `LLONG_MIN` after the loop (e.g., all elements were identical), output `-1`.

### Output & Verification
<img width="1470" height="956" alt="Screenshot 2026-09-05 at 11 53 52 PM" src="https://github.com/user-attachments/assets/f1091d13-dc4a-4887-8f48-69e6af397b2d" />
