#[derive(Debug)]
pub struct Node<T> {
    value: T,
    next: Option<*mut Node<T>>,
    prev: Option<*mut Node<T>>,
}

pub struct DoublyLinkedList<T> {
    head: Option<*mut Node<T>>,
    tail: Option<*mut Node<T>>,
    length: usize,
}

impl<T> DoublyLinkedList<T> {
    pub fn new() -> Self {
        DoublyLinkedList {
            head: None,
            tail: None,
            length: 0,
        }
    }

    pub fn push_front(&mut self, value: T) {
        let new_node = Box::into_raw(Box::new(Node {
            value,
            next: self.head,
            prev: None,
        }));

        unsafe {
            if let Some(head) = self.head {
                (*head).prev = Some(new_node);
            } else {
                self.tail = Some(new_node);
            }
        }
        
        self.head = Some(new_node);
        self.length += 1;
    }

    pub fn push_back(&mut self, value: T) {
        let new_node = Box::into_raw(Box::new(Node {
            value,
            next: None,
            prev: self.tail,
        }));

        unsafe {
            if let Some(tail) = self.tail {
                (*tail).next = Some(new_node);
            } else {
                self.head = Some(new_node);
            }
        }
        
        self.tail = Some(new_node);
        self.length += 1;
    }

    pub fn pop_front(&mut self) -> Option<T> {
        self.head.map(|head| unsafe {
            let head_box = Box::from_raw(head);
            
            if let Some(next) = head_box.next {
                (*next).prev = None;
                self.head = Some(next);
            } else {
                // Era el único nodo
                self.head = None;
                self.tail = None;
            }
            
            self.length -= 1;
            head_box.value
        })
    }

    pub fn pop_back(&mut self) -> Option<T> {
        self.tail.map(|tail| unsafe {
            let tail_box = Box::from_raw(tail);
            
            if let Some(prev) = tail_box.prev {
                (*prev).next = None;
                self.tail = Some(prev);
            } else {
                self.head = None;
                self.tail = None;
            }
            
            self.length -= 1;
            tail_box.value
        })
    }

    // CORREGIDO: Ahora retorna Option<&T> en lugar de Option<*mut Node<T>>
    pub fn find(&self, value: &T) -> Option<&T> 
    where 
        T: PartialEq 
    {
        // Necesitamos implementar el iterador primero
        let mut current = self.head;
        while let Some(node_ptr) = current {
            unsafe {
                if &(*node_ptr).value == value {
                    return Some(&(*node_ptr).value);
                }
                current = (*node_ptr).next;
            }
        }
        None
    }

    // Versión que encuentra y retorna referencia mutable
    pub fn find_mut(&mut self, value: &T) -> Option<&mut T> 
    where 
        T: PartialEq 
    {
        let mut current = self.head;
        while let Some(node_ptr) = current {
            unsafe {
                if &(*node_ptr).value == value {
                    return Some(&mut (*node_ptr).value);
                }
                current = (*node_ptr).next;
            }
        }
        None
    }

    // Implementación del iterador
    pub fn iter(&self) -> Iter<'_, T> {
        Iter { 
            next: self.head.map(|ptr| unsafe { &*ptr }) 
        }
    }

    // Iterador mutable
    pub fn iter_mut(&mut self) -> IterMut<'_, T> {
        IterMut { 
            next: self.head.map(|ptr| unsafe { &mut *ptr }) 
        }
    }

    // Iterador reverso
    pub fn iter_rev(&self) -> IterRev<'_, T> {
        IterRev { 
            prev: self.tail.map(|ptr| unsafe { &*ptr }) 
        }
    }

    pub fn front(&self) -> Option<&T> {
        self.head.map(|head| unsafe { &(*head).value })
    }

    pub fn back(&self) -> Option<&T> {
        self.tail.map(|tail| unsafe { &(*tail).value })
    }

    pub fn front_mut(&mut self) -> Option<&mut T> {
        self.head.map(|head| unsafe { &mut (*head).value })
    }

    pub fn back_mut(&mut self) -> Option<&mut T> {
        self.tail.map(|tail| unsafe { &mut (*tail).value })
    }

    pub fn len(&self) -> usize {
        self.length
    }

    pub fn is_empty(&self) -> bool {
        self.length == 0
    }

    // Método para limpiar la lista
    pub fn clear(&mut self) {
        while self.pop_front().is_some() {}
    }
}

// Iterador forward
pub struct Iter<'a, T> {
    next: Option<&'a Node<T>>,
}

impl<'a, T> Iterator for Iter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        self.next.map(|node| {
            self.next = node.next.map(|next_ptr| unsafe { &*next_ptr });
            &node.value
        })
    }
}

// Iterador forward mutable
pub struct IterMut<'a, T> {
    next: Option<&'a mut Node<T>>,
}

impl<'a, T> Iterator for IterMut<'a, T> {
    type Item = &'a mut T;

    fn next(&mut self) -> Option<Self::Item> {
        self.next.take().map(|node| {
            self.next = node.next.map(|next_ptr| unsafe { &mut *next_ptr });
            &mut node.value
        })
    }
}

// Iterador reverso
pub struct IterRev<'a, T> {
    prev: Option<&'a Node<T>>,
}

impl<'a, T> Iterator for IterRev<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        self.prev.map(|node| {
            self.prev = node.prev.map(|prev_ptr| unsafe { &*prev_ptr });
            &node.value
        })
    }
}

impl<T> Drop for DoublyLinkedList<T> {
    fn drop(&mut self) {
        while self.pop_front().is_some() {}
    }
}

// Implementación de Clone
impl<T: Clone> Clone for DoublyLinkedList<T> {
    fn clone(&self) -> Self {
        let mut new_list = Self::new();
        for item in self.iter() {
            new_list.push_back(item.clone());
        }
        new_list
    }
}

// Implementación de Debug
impl<T: std::fmt::Debug> std::fmt::Debug for DoublyLinkedList<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_list().entries(self.iter()).finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_doubly_linked_basic() {
        let mut list = DoublyLinkedList::new();
        
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        assert_eq!(list.len(), 3);
        assert_eq!(list.front(), Some(&1));
        assert_eq!(list.back(), Some(&3));
        
        assert_eq!(list.pop_front(), Some(1));
        assert_eq!(list.pop_back(), Some(3));
        assert_eq!(list.pop_front(), Some(2));
        assert_eq!(list.pop_front(), None);
    }

    #[test]
    fn test_push_pop_both_ends() {
        let mut list = DoublyLinkedList::new();
        
        list.push_front(2);
        list.push_front(1);
        list.push_back(3);
        list.push_back(4);
        
        assert_eq!(list.pop_front(), Some(1));
        assert_eq!(list.pop_back(), Some(4));
        assert_eq!(list.pop_front(), Some(2));
        assert_eq!(list.pop_back(), Some(3));
        assert_eq!(list.pop_front(), None);
    }

    #[test]
    fn test_find() {
        let mut list = DoublyLinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        // CORREGIDO: Ahora find retorna Option<&T>
        assert_eq!(list.find(&2), Some(&2));
        assert_eq!(list.find(&4), None);
        
        // Test find_mut
        if let Some(value) = list.find_mut(&2) {
            *value = 20;
        }
        assert_eq!(list.find(&20), Some(&20));
    }

    #[test]
    fn test_iterators() {
        let mut list = DoublyLinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        // Test iter forward
        let forward: Vec<&i32> = list.iter().collect();
        assert_eq!(forward, vec![&1, &2, &3]);
        
        // Test iter reverse
        let reverse: Vec<&i32> = list.iter_rev().collect();
        assert_eq!(reverse, vec![&3, &2, &1]);
        
        // Test iter mut
        for value in list.iter_mut() {
            *value *= 2;
        }
        let doubled: Vec<&i32> = list.iter().collect();
        assert_eq!(doubled, vec![&2, &4, &6]);
    }

    #[test]
    fn test_clear() {
        let mut list = DoublyLinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        assert_eq!(list.len(), 3);
        list.clear();
        assert_eq!(list.len(), 0);
        assert!(list.is_empty());
    }

    #[test]
    fn test_front_back_mut() {
        let mut list = DoublyLinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        if let Some(front) = list.front_mut() {
            *front = 10;
        }
        if let Some(back) = list.back_mut() {
            *back = 30;
        }
        
        assert_eq!(list.front(), Some(&10));
        assert_eq!(list.back(), Some(&30));
    }

    #[test]
    fn test_generic_types() {
        #[derive(Debug, PartialEq)]
        struct Point {
            x: i32,
            y: i32,
        }
        let mut list = DoublyLinkedList::new();
        list.push_back(Point { x: 1, y: 2 });
        list.push_back(Point { x: 3, y: 4 });

        assert_eq!(list.len(), 2);
        assert_eq!(list.pop_front(), Some(Point { x: 1, y: 2 }));
        assert_eq!(list.pop_back(), Some(Point { x: 3, y: 4 }));
    }
}