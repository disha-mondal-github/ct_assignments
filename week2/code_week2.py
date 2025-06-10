class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def add_node(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            print(f"Added {data} as the head node.")
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
            print(f"Added {data} to the end of the list.")

    def print_list(self):
        if not self.head:
            print("The list is empty.")
        else:
            current = self.head
            print("Linked List: ", end="")
            while current:
                print(current.data, end=" -> ")
                current = current.next
            print("None")

    def delete_nth_node(self, n):
        if not self.head:
            raise Exception("Cannot delete from an empty list.")
        if n <= 0:
            raise Exception("Invalid index. Please provide a positive integer.")
        if n == 1:
            print(f"Deleting node at position {n} with value {self.head.data}")
            self.head = self.head.next
            return
        current = self.head
        for i in range(n - 2):
            if current.next is None:
                raise Exception(f"Index {n} is out of range.")
            current = current.next
        if current.next is None:
            raise Exception(f"Index {n} is out of range.")
        print(f"Deleting node at position {n} with value {current.next.data}")
        current.next = current.next.next

ll = LinkedList()

while True:
    print("\nOptions:")
    print("1. Add node")
    print("2. Print list")
    print("3. Delete nth node")
    print("4. Exit")

    choice = input("Enter your choice (1-4): ")

    if choice == '1':
        try:
            data = int(input("Enter the value to add: "))
            ll.add_node(data)
        except ValueError:
            print("Invalid input. Please enter an integer.")
    elif choice == '2':
        ll.print_list()
    elif choice == '3':
        try:
            n = int(input("Enter the position of the node to delete (1-based index): "))
            ll.delete_nth_node(n)
        except ValueError:
            print("Invalid input. Please enter a positive integer.")
        except Exception as e:
            print("Error:", e)
    elif choice == '4':
        print("Exiting program.")
        break
    else:
        print("Invalid choice. Please enter a number between 1 and 4.")