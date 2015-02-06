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

(defun second (lst)
  (first (rest lst)))

(defun ffirst (lst)
  (first (first lst)))

(defun rfirst (lst)
  (rest (first lst)))

(defun firsts (lists)
  (mapf (fn (l) (first l)) lists))

(defun rests (lists)
  (mapf (fn (l) (rest l)) lists))

(defun any (values)
  (if (null values)
      '()
      (if (first values)
          't
          (any (rest values)))))

(defun all (values)
  (if (null values)
      't
      (if (first values)
          (all (rest values))
          '())))

(defun zip1 (lists)
  (if (any (mapf null lists))
      '()
      (prep (firsts lists) (zip1 (rests lists)))))

(defun zip (&rest lists)
  (zip1 lists))

(defmac let (pairs form)
  (prep (list 'fn (firsts pairs) form)
        (mapf second pairs)))

(defun cond1 (pairs)
  (if (null pairs)
      '()
      (list 'if
            (ffirst pairs)
            (second (first pairs))
            (list 'cond (rest pairs)))))

(defmac cond (&rest pairs)
  (cond1 pairs))

(defmac when (condition body)
  (list 'if condition body '()))

(defun atom (value)
  (if (eq (typeof value) 'list)
      '()
      't))

(defun first (lst)
  (first lst))

(defun rest (lst)
  (rest lst))

(defun typeof (value)
  (typeof value))

(defun eq (value1 value2)
  (eq value1 value2))

(defun prep (val lst)
  (prep val lst))

(defun apply (func args)
  (apply func args))
