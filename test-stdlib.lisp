;; not
(eq (not 't) nil)
(eq (not nil) 't)

;; =
(= 1 1)
(= 'x 'x)
(= "foo" "foo")
(not (= 1 2))
(not (= "foo" "Foo"))
(not (= 'foo "foo"))
(not (= 10 "10"))
(= nil nil)
(= '(1) '(1))
(= '(10 20) '(10 20))
(= '(1 (2 3) 'foo ()) '(1 (2 3) 'foo ()))
(not (= '(1) '(1 2)))

;; list
(= (list) '())
(= (list 1 'x "foo") '(1 x "foo"))

;; null
(eq (null nil) 't)
(eq (null '(1 2 3)) nil)

;; and
(and)
(and 't)
(and 't 't)
(and 't 't 't)
(not (and 't nil 't 't))
(not (and nil))
(not (and nil 't))
(not (and 't nil))
(not (and nil nil))

;; or
(not (or))
(or 't)
(not (or nil))
(or 't 't)
(or 't 't 't 't)
(or 't 't 't nil 't)
(not (or nil nil nil))
(or 't nil)
(or nil 't)
(not (or nil nil))

;; append
(= (append '(1 2) '(3 4))
   '(1 2 3 4))
(= (append nil '(1 2))
   '(1 2))
(= (append '(1 2) nil)
   '(1 2))
(= (append '(1) '(2 3))
   '(1 2 3))
(= (append '(1 2) '(3))
   '(1 2 3))

;; mapf
(= (mapf null '(1 2 '(1) () '(x y)))
   '(() () () t ()))
(= (mapf first '((1 2) (x y) ("foo" 10 20)))
   '(1 x "foo"))

;; remove-if
(= (remove-if null '(1 2 () 3 (x y)))
   '(1 2 3 (x y)))
(= (remove-if null nil)
   nil)

;; second
(= (second '(1 2 3)) 2)

;; ffirst
(= (ffirst '((1 2) 3 4))
   1)

;; rfirst
(= (rfirst '((1 2) 3 4))
   '(2))

;; firsts
(= (firsts '((1 2 3) (x y z)))
   '(1 x))

(= (firsts '((1 2 3)))
   '(1))

(= (firsts nil) nil)

;; rests
(= (rests '((1 2 3) (x y z)))
   '((2 3) (y z)))

(= (rests '((1 2 3)))
   '((2 3)))

(= (rests nil) nil)

;; any
(not (any nil))
(any (list nil nil nil 't nil))
(any (list 't))
(not (any (list nil)))
(not (any (list nil nil nil)))

;; all
(all nil)
(all (list 't 't 't 't 'x "foo" 12))
(not (all (list nil)))
(not (all (list nil nil 't nil)))
(not (all (list 't 't nil 't)))

;; zip
(= (zip) nil)
(= (zip nil nil nil) nil)
(= (zip '(1))
   '((1)))
(= (zip '(1 2) '(a b) '("foo" "bar"))
   '((1 a "foo") (2 b "bar")))

;; let
(let ((x 2)
      (y 'foo)
      (z "bar"))
  (and (= x 2)
       (= y 'foo)
       (= z "bar")))

;; cond
(not (cond))
(= 100
   (cond ('t 100)
         ('t 200)))
(= 200
   (cond (nil 100)
         ('t 200)))
(= 400
   (cond (nil 100)
         (nil 200)
         (nil 300)
         ('t 400)))

;; when
(= 100
   (when 't
     100))
(= nil
   (when nil
     100))

;; atom
(atom 'x)
(atom 10)
(atom "foo")
(not (atom nil))
(not (atom '(1)))
(not (atom '(1 2 3)))

;; map
(let ((foo (fn (x y) (list y x))))
  (= (map foo '(10 20) '(foo bar))
     '((foo 10) (bar 20))))
(= (map (fn () 10)) nil)
