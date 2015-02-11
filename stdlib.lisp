(define list (fn (&rest items)
                 items))

(define defun (mac (name args body)
                   (list 'define name (list 'fn args body))))

(define defmac (mac (name args body)
                    (list 'define name (list 'mac args body))))

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

(defun null (v)
  (if v '() 't))

(defun not (v)
  (if v '() 't))

(defun and (&rest values)
  (all values))

(defun or (&rest values)
  (any values))

(defun append2 (l1 l2)
  (if (null l1)
      l2
      (prep (first l1) (append2 (rest l1) l2))))

(defun append1 (lists)
  (if (null lists)
      nil
      (append2 (first lists)
               (append1 (rest lists)))))

(defun append (&rest lists)
  (append1 lists))

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
  (mapf first lists))

(defun rests (lists)
  (mapf rest lists))

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
  (if (or (null lists)
          (any (mapf null lists)))
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
            (prep 'cond (rest pairs)))))

(defmac cond (&rest pairs)
  (cond1 pairs))

(defmac when (condition body)
  (list 'if condition body '()))

(defun atom (value)
  (if (eq (typeof value) 'list)
      '()
      't))

(defun map1 (func args_list)
  (if (or (null args_list)
          (any (mapf null args_list)))
      '()
      (prep (apply func (firsts args_list))
            (map1 func (rests args_list)))))

(defun map (func &rest args_list)
  (map1 func args_list))

(defun = (v1 v2)
  (cond ((not (eq (typeof v1) (typeof v2)))
         nil)
        ((and (atom v1) (atom v2))
         (eq v1 v2))
        ((and (null v1) (null v2))
         't)
        ((and (null v1) (not (null v2)))
         nil)
        ((and (null v2) (not (null v1)))
         nil)
        ('t
         (and (= (first v1) (first v2))
              (= (rest v1) (rest v2))))))
