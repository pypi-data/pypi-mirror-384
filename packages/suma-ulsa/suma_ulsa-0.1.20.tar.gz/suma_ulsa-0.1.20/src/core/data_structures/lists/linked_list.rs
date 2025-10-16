use std::fmt;

#[derive(Debug, Clone)]
pub struct Node<T> {
    value: T,
    next: Option<Box<Node<T>>>,
}

#[derive(Debug)]
pub struct LinkedList<T> {
    head: Option<Box<Node<T>>>,
    tail: *mut Node<T>,
    length: usize,
}

impl<T> LinkedList<T> {
    pub fn new() -> Self {
        LinkedList {
            head: None,
            tail: std::ptr::null_mut(),
            length: 0,
        }
    }

    pub fn push_front(&mut self, value: T) {
        let new_node = Box::new(Node {
            value,
            next: self.head.take(),
        });
        
        if self.tail.is_null() {
            let raw_node: *mut _ = Box::into_raw(new_node);
            self.tail = raw_node;
            self.head = unsafe { Some(Box::from_raw(raw_node)) };
        } else {
            self.head = Some(new_node);
        }
        self.length += 1;
    }

    pub fn push_back(&mut self, value: T) {
        let mut new_node = Box::new(Node { value, next: None });
        let raw_node: *mut _ = &mut *new_node;

        if self.tail.is_null() {
            self.head = Some(new_node);
            self.tail = raw_node;
        } else {
            unsafe {
                (*self.tail).next = Some(new_node);
            }
            self.tail = raw_node;
        }
        self.length += 1;
    }

    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|node| {
            self.head = node.next;
            if self.head.is_none() {
                self.tail = std::ptr::null_mut();
            }
            self.length -= 1;
            node.value
        })
    }

    // Pop back es más complejo en lista simplemente enlazada
    pub fn pop_back(&mut self) -> Option<T> {
        if self.head.is_none() {
            return None;
        }
        
        if self.length == 1 {
            return self.pop_front();
        }
        
        // Encontrar el penúltimo nodo
        let mut current = &mut self.head;
        while current.as_ref().unwrap().next.is_some() {
            current = &mut current.as_mut().unwrap().next;
        }
        
        let last_node = current.take().unwrap();
        self.tail = current as *mut _ as *mut Node<T>;
        self.length -= 1;
        Some(last_node.value)
    }

    pub fn front(&self) -> Option<&T> {
        self.head.as_ref().map(|node| &node.value)
    }

    pub fn back(&self) -> Option<&T> {
        if self.tail.is_null() {
            None
        } else {
            unsafe { Some(&(*self.tail).value) }
        }
    }

    pub fn contains(&self, value: &T) -> bool 
    where 
        T: PartialEq,
    {
        self.iter().any(|v| v == value)
    }

    pub fn find(&self, value: &T) -> Option<&T> 
    where 
        T: PartialEq,
    {
        self.iter().find(|&v| v == value)
    }

    pub fn clear(&mut self) {
        *self = Self::new();
    }

    // Iterador inmutable
    pub fn iter(&self) -> Iter<'_, T> {
        Iter { next: self.head.as_deref() }
    }

    pub fn len(&self) -> usize {
        self.length
    }

    pub fn is_empty(&self) -> bool {
        self.length == 0
    }

    pub fn reverse(&mut self) {
        let mut prev = None;
        let mut current = self.head.take();
        self.tail = std::ptr::null_mut();

        while let Some(mut node) = current {
            let next = node.next.take();
            node.next = prev;
            if self.tail.is_null() {
                self.tail = &mut *node;
            }
            prev = Some(node);
            current = next;
        }
        self.head = prev;
    }

}

// Implementación del iterador
pub struct Iter<'a, T> {
    next: Option<&'a Node<T>>,
}

impl<'a, T> Iterator for Iter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        self.next.map(|node| {
            self.next = node.next.as_deref();
            &node.value
        })
    }
}

// Implementación de Drop para evitar memory leaks
impl<T> Drop for LinkedList<T> {
    fn drop(&mut self) {
        let mut current = self.head.take();
        while let Some(mut node) = current {
            current = node.next.take();
        }
    }
}

// Implementación de Clone manual (más eficiente)
impl<T: Clone> Clone for LinkedList<T> {
    fn clone(&self) -> Self {
        let mut new_list = Self::new();
        for item in self.iter() {
            new_list.push_back(item.clone());
        }
        new_list
    }
}

// Implementación de Display
impl<T: fmt::Display> fmt::Display for LinkedList<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut first = true;
        for item in self.iter() {
            if first {
                first = false;
            } else {
                write!(f, " -> ")?;
            }
            write!(f, "[{}]", item)?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_operations() {
        let mut list = LinkedList::new();
        
        // Test push_back y len
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        assert_eq!(list.len(), 3);
        assert!(!list.is_empty());
        
        // Test front y back
        assert_eq!(list.front(), Some(&1));
        assert_eq!(list.back(), Some(&3));
        
        // Test pop_front
        assert_eq!(list.pop_front(), Some(1));
        assert_eq!(list.len(), 2);
        assert_eq!(list.front(), Some(&2));
    }

    #[test]
    fn test_push_front() {
        let mut list = LinkedList::new();
        list.push_front(3);
        list.push_front(2);
        list.push_front(1);
        
        assert_eq!(list.len(), 3);
        assert_eq!(list.front(), Some(&1));
        assert_eq!(list.back(), Some(&3));
        
        assert_eq!(list.pop_front(), Some(1));
        assert_eq!(list.pop_front(), Some(2));
        assert_eq!(list.pop_front(), Some(3));
        assert_eq!(list.pop_front(), None);
    }

    #[test]
    fn test_pop_back() {
        let mut list = LinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        assert_eq!(list.pop_back(), Some(3));
        assert_eq!(list.back(), Some(&2));
        assert_eq!(list.len(), 2);
        
        assert_eq!(list.pop_back(), Some(2));
        assert_eq!(list.pop_back(), Some(1));
        assert_eq!(list.pop_back(), None);
    }

    #[test]
    fn test_contains_and_find() {
        let mut list = LinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        assert!(list.contains(&2));
        assert!(!list.contains(&4));
        assert_eq!(list.find(&3), Some(&3));
        assert_eq!(list.find(&5), None);
    }

    #[test]
    fn test_iterator() {
        let mut list = LinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        let mut iter = list.iter();
        assert_eq!(iter.next(), Some(&1));
        assert_eq!(iter.next(), Some(&2));
        assert_eq!(iter.next(), Some(&3));
        assert_eq!(iter.next(), None);
        
        // Test colectar a Vec
        let collected: Vec<&i32> = list.iter().collect();
        assert_eq!(collected, vec![&1, &2, &3]);
    }

    #[test]
    fn test_clear() {
        let mut list = LinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        assert_eq!(list.len(), 3);
        list.clear();
        assert_eq!(list.len(), 0);
        assert!(list.is_empty());
        assert_eq!(list.front(), None);
        assert_eq!(list.back(), None);
    }


    #[test]
    fn test_display() {
        let mut list = LinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        assert_eq!(format!("{}", list), "[1] -> [2] -> [3]");
        println!("{}", list); // Para ver la salida en consola
    }

    #[test]
    fn test_empty_list() {
        let mut list: LinkedList<i32> = LinkedList::new();
        assert_eq!(list.len(), 0);
        assert!(list.is_empty());
        assert_eq!(list.front(), None);
        assert_eq!(list.back(), None);
        assert_eq!(list.pop_front(), None);
        assert_eq!(list.pop_back(), None);
    }
    
    #[test]
    fn test_reverse() {
        let mut list = LinkedList::new();
        list.push_back(1);
        list.push_back(2);
        list.push_back(3);
        
        list.reverse();
        
        assert_eq!(list.front(), Some(&3));
        assert_eq!(list.back(), Some(&1));
        
        let collected: Vec<&i32> = list.iter().collect();
        assert_eq!(collected, vec![&3, &2, &1]);
    }
}