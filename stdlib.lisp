(define list (fn (& items)
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

(defun iadd (n m)
  (iadd n m))

(defun imul (n m)
  (imul n m))

(defun idiv (n m)
  (idiv n m))

(defun imod (n m)
  (imod n m))

(defun ineg (n)
  (ineg n m))

(defun null (v)
  (if (eq v nil) #t #f))

(defun not (v)
  (if v #f #t))

(defun and (& values)
  (all values))

(defun or (& values)
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

(defun append (& lists)
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

(defun frest (lst)
  (first (rest lst)))

(defun rrest (lst)
  (rest (rest lst)))

(defun rfirst (lst)
  (rest (first lst)))

(defun last (lst)
  (cond ((atom lst)
         (error :type-error
                :msg "The argument to last must be a list."
                :form lst))
        ((null lst)
         (error :value-error
                :msg "The argument to last cannot be an empty list."
                :form lst))
        ((null (rest lst)) (first lst))
        (#t (last (rest lst)))))

(defun butlast (lst)
  (cond ((atom lst) :#ERROR#:)
        ((null lst) :#ERROR#:)
        ((null (rest lst)) nil)
        (#t (prep (first lst) (butlast (rest lst))))))

(defun firsts (lists)
  (mapf first lists))

(defun rests (lists)
  (mapf rest lists))

(defun any (values)
  (if (null values)
      #f
      (if (first values)
          #t
          (any (rest values)))))

(defun all (values)
  (if (null values)
      #t
      (if (first values)
          (all (rest values))
          #f)))

(defun zip1 (lists)
  (if (or (null lists)
          (any (mapf null lists)))
      '()
      (prep (firsts lists) (zip1 (rests lists)))))

(defun zip (& lists)
  (zip1 lists))

(defmac let (pairs form)
  (prep (list 'fn (firsts pairs) form)
        (mapf second pairs)))

(defmac let* (pairs form)
  (if (null pairs)
      form
      (list (list 'fn
                  (list (ffirst pairs))
                  (list 'let* (rest pairs) form))
            (second (first pairs)))))

(defun cond1 (pairs)
  (if (null pairs)
      #f
      (list 'if
            (ffirst pairs)
            (second (first pairs))
            (prep 'cond (rest pairs)))))

(defmac cond (& pairs)
  (cond1 pairs))

(defmac when (condition body)
  (list 'if condition body '()))

(defun atom (value)
  (not (eq (typeof value) 'list)))

(defun map1 (func args_list)
  (if (or (null args_list)
          (any (mapf null args_list)))
      '()
      (prep (apply func (firsts args_list))
            (map1 func (rests args_list)))))

(defun map (func & args_list)
  (map1 func args_list))

(defun = (v1 v2)
  (cond ((not (eq (typeof v1) (typeof v2)))
         #f)
        ((and (atom v1) (atom v2))
         (eq v1 v2))
        ((and (null v1) (null v2))
         #t)
        ((and (null v1) (not (null v2)))
         #f)
        ((and (null v2) (not (null v1)))
         #f)
        (#t
         (and (= (first v1) (first v2))
              (= (rest v1) (rest v2))))))

(defun eval (form)
  ((mac () form)))

(defun assoc (key alist)
  (cond ((atom alist) :#ERROR-INVALID#:)
        ((null alist) :#ERROR-NOT-FOUND#:)
        ((null (rest alist)) :#ERROR-INVALID#:)
        ((= (first alist) key) (frest alist))
        (#t (assoc key (rrest alist)))))

(defun remove (item lst)
  (if (null lst)
      nil
      (if (= item (first lst))
          (remove item (rest lst))
          (prep (first lst) (remove item (rest lst))))))
(defun construct-try-clauses (catch-clauses)
  (cond ((null catch-clauses) nil)
        ((atom (first catch-clauses))
         (error :form-error :msg "try catch clauses must be lists." :form (first catch-clauses)))
        ((null (first catch-clauses))
         (error :form-error :msg "try catch clauses must be two element lists." :form (first catch-clauses)))
        ((null (rfirst catch-clauses))
         (error :form-error :msg "try catch clauses must be two element lists." :form (first catch-clauses)))
        (#t (prep `((= it ,(ffirst catch-clauses))
                    ,(second (first catch-clauses)))
                  (construct-try-clauses (rest catch-clauses))))))

(defmac try (form & catch-clauses)
  `(let ((it ,form))
     (if (eq (typeof it) 'error)
         (let ((it (error-type it)))
           (cond ,@(construct-try-clauses catch-clauses)
                 (#t (error :catch-error :msg "No catch clause matched." :form catch-clauses))))
         it)))

(defun symbol? (v)
  (eq (typeof v) 'symbol))

(defun list? (v)
  (eq (typeof v) 'list))

(defun string? (v)
  (eq (typeof v) 'str))

(defun reduce (f lst)
  (cond ((not (eq (typeof f) 'function))
         (error :type-error))
        ((atom lst)
         (error :type-error))
        ((null lst)
         (error :value-error))
        ((null (rest lst))
         (first lst))
        ((null (rrest lst))
         (f (first lst) (second lst)))
        (#t
         (f (first lst) (reduce f (rest lst))))))

(defun + (& values)
  (cond ((null values)
         0)
        (#t
         (iadd (first values) (apply + (rest values))))))

(defun - (& values)
  (cond ((null values)
         0)
        ((null (rest values))
         (ineg (first values)))
        (#t
         (iadd (first values)
               (ineg (apply + (rest values)))))))

(defun * (& values)
  (cond ((null values)
         1)
        (#t
         (imul (first values) (apply * (rest values))))))

(defun ++ (n)
  (iadd n 1))

(defun -- (n)
  (iadd n -1))
