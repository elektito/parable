(defun bq-simplify (form)
  ;; if there's an append in which all arguments are single lengthed
  ;; lists, convert it to a "list" call:
  ;; (append '(x) (list y) '(z)) => (list 'x y 'z)
  ;;
  ;; if there is a list call in which all forms are quoted, convert it
  ;; to a single quoted list:
  ;; (list 'x 'y 'z) => '(x y z)
  form)

(defun bq-is-unquote (form)
  (cond ((atom form) #f)
        ((null form) #f)
        ((eq (first form) 'unquote) #t)
        (#t #f)))

(defun bq-is-unquote-splicing (form)
  (cond ((atom form) #f)
        ((null form) #f)
        ((eq (first form) 'unquote-splicing) #t)
        (#t #f)))

(defun bq-is-backquote (form)
  (cond ((atom form) #f)
        ((null form) #f)
        ((eq (first form) 'backquote) #t)
        (#t #f)))

(defun bq-process-list-item (form level)
  (cond ((atom form)
         (list 'quote (list form)))
        ((bq-is-unquote form)
         (if (= level 1)
             (list 'list (second form))
             (list 'list (bq-process-list form (-- level)))))
        ((bq-is-unquote-splicing form)
         (second form))
        ((bq-is-backquote form)
         (list 'list
               (bq-process-list form (++ level))))
        (#t
         (list 'list
               (bq-process-list form level)))))

(defun bq-process-list (form level)
  (prep 'append
        (mapf (fn (form)
                (bq-process-list-item form level))
              form)))

(defun bq-process (form level)
  (cond ((atom form)
         (if (= level 1)
             (list 'quote form)
             form))
        ((bq-is-unquote form)
         (if (= level 1)
             (second form)
             (bq-process-list form (-- level))))
        ((bq-is-unquote-splicing form)
         (list 'quote '#:ERROR:#))
        ((bq-is-backquote form)
         (bq-process-list form (++ level)))
        (#t
         (bq-process-list form level))))

(defmac backquote (form)
  (bq-simplify
   (bq-process form 1)))
