(define list (fn (&rest items)
                 items))

(define defun (mac (name args body)
                   (list 'define name (list 'fn args body))))

(define defmac (mac (name args body)
                    (list 'define name (list 'mac args body))))

(defun null (v)
  (if v '() 't))

(defun not (v)
  (if v '() 't))

(defun and (u v)
  (if u (if v 't '()) '()))

(defun or (u v)
  (if u 't (if v 't '())))

(defun append (l1 l2)
  (if (null l1)
      l2
      (prep (first l1) (append (rest l1) l2))))

(defun mapf (func args)
  (if (null args)
      '()
      (prep (func (first args))
            (mapf func (rest args)))))

(defun remove-if (func lst)
  (if (null lst)
      '()
      (if (func (first lst))
          (remove-if func (rest lst))
          (prep (first lst) (remove-if func (rest lst))))))

(defun ffirst (lst)
  (first (first lst)))

(defun firsts (lists)
  (if (null lists)
      '()
      (prep (ffirst lists) (firsts (rest lists)))))
