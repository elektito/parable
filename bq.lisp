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

(defun bq-process-list-item (form)
  (cond ((atom form)
         (list 'quote (list form)))
        ((bq-is-unquote form)
         (list 'list (second form)))
        ((bq-is-unquote-splicing form)
         (second form))
        ((bq-is-backquote form)
         (list 'quote (list '#:ERROR:NESTED-BACKQUOTES:#)))
        (#t
         (list 'list
               (bq-process-list form)))))

(defun bq-process-list (form)
  (prep 'append
        (mapf bq-process-list-item form)))

(defun bq-process (form)
  (cond ((atom form)
         (list 'quote form))
        ((bq-is-unquote form)
         (second form))
        ((bq-is-unquote-splicing form)
         (list 'quote '#:ERROR:#))
        ((bq-is-backquote form)
         (list 'quote '#:ERROR:NESTED-BACKQUOTES:#))
        (#t
         (bq-process-list form))))

(defmac backquote (form)
  (bq-simplify
   (bq-process form)))
