--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: predictions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.predictions (
    id integer NOT NULL,
    user_id integer,
    regularity double precision,
    revenue double precision,
    average_revenue_per_user double precision,
    frequence double precision,
    data_volume double precision,
    frequence_rech double precision,
    total_amount_spent double precision,
    prediction integer,
    confidence integer,
    churn_status character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.predictions OWNER TO postgres;

--
-- Name: predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.predictions_id_seq OWNER TO postgres;

--
-- Name: predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.predictions_id_seq OWNED BY public.predictions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone,
    first_name character varying(50),
    last_name character varying(50),
    role character varying(20) DEFAULT 'user'::character varying
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: predictions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions ALTER COLUMN id SET DEFAULT nextval('public.predictions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: predictions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.predictions (id, user_id, regularity, revenue, average_revenue_per_user, frequence, data_volume, frequence_rech, total_amount_spent, prediction, confidence, churn_status, created_at) FROM stdin;
1	1	0	0	0	0	0	0	0	1	99	HIGH CHURN RISK	2025-07-09 10:42:20.718399
2	1	5	2000	2000	1	1	2	2000	0	99	LOW CHURN RISK	2025-07-09 10:43:37.891579
3	1	1	2000	2000	1	1	2	2000	1	99	HIGH CHURN RISK	2025-07-09 10:44:12.365197
4	1	3	3500	4000	3	1	2	5000	0	92	LOW CHURN RISK	2025-07-09 10:48:24.126036
5	1	2	3500	4000	3	1	2	5000	0	92	LOW CHURN RISK	2025-07-09 10:48:56.312263
6	1	1	3500	4000	3	1	2	5000	1	98	HIGH CHURN RISK	2025-07-09 10:49:04.280715
7	1	1	50000	25000	5	4	4	5000	1	90	HIGH CHURN RISK	2025-07-09 10:49:46.564609
8	1	4	50	20	1	1	1	35	1	61	HIGH CHURN RISK	2025-07-09 10:50:31.811598
9	1	10	50	20	1	1	1	35	1	61	HIGH CHURN RISK	2025-07-09 10:50:42.348056
10	1	10	50	20	5	1	1	35	0	98	LOW CHURN RISK	2025-07-09 10:50:52.070162
11	1	4	50000	25000	5	4	4	5000	0	99	LOW CHURN RISK	2025-07-09 10:54:13.155446
12	1	6	5000	2500	5	4	4	500	0	99	LOW CHURN RISK	2025-07-09 10:54:30.819125
13	1	2	5000	2500	2	4	4	500	0	99	LOW CHURN RISK	2025-07-09 10:54:41.071328
14	1	1	5000	2500	2	5	4	500	1	97	HIGH CHURN RISK	2025-07-09 10:54:51.738935
15	1	3	5000	2500	2	5	4	500	0	99	LOW CHURN RISK	2025-07-09 10:54:59.018811
16	2	3	1500	1500	2	2	1	1500	0	89	LOW CHURN RISK	2025-07-09 16:11:42.094384
17	1	2	1500	1500	2	2	1	1500	0	89	LOW CHURN RISK	2025-07-09 16:41:46.033821
18	1	2	1500	1500	2	2	1	1500	0	89	LOW CHURN RISK	2025-07-09 16:41:52.945554
19	1	1	1500	1500	2	2	1	1500	1	99	HIGH CHURN RISK	2025-07-09 16:42:02.144385
20	2	3	2000	2000	1	3	1	2000	1	60	HIGH CHURN RISK	2025-07-10 03:18:00.023857
21	2	3	2000	2000	2	3	2	2000	0	96	LOW CHURN RISK	2025-07-10 03:18:46.689623
22	1	3	2000	2000	1	3	1	2000	1	60	HIGH CHURN RISK	2025-07-10 03:27:50.023957
23	1	3	2000	2000	1	3	2	2000	0	99	LOW CHURN RISK	2025-07-10 03:34:12.405039
24	1	3	2000	2000	2	3	1	2000	0	85	LOW CHURN RISK	2025-07-10 03:37:22.800918
25	1	3	2000	2000	2	3	1	2000	0	85	LOW CHURN RISK	2025-07-10 03:37:29.482994
26	1	3	2000	2000	2	3	1	2000	0	85	LOW CHURN RISK	2025-07-10 03:39:06.674731
27	1	3	2000	2000	2	3	1	2000	0	85	LOW CHURN RISK	2025-07-10 03:40:46.811569
28	1	1	2000	2000	3	2	4	2000	1	96	HIGH CHURN RISK	2025-07-10 04:32:03.070352
29	1	1	2000	2000	3	2	4	2000	1	96	HIGH CHURN RISK	2025-07-10 05:16:30.217279
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, email, password_hash, created_at, last_login, first_name, last_name, role) FROM stdin;
2	BQ	blessingsqabaniso@gmail.com	$2b$12$u1ScYTUPs2XypjKH2EFAuOn/.mmW/cm7KcIHbFByP854RJfL0uYW2	2025-07-09 16:07:16.799738	2025-07-10 03:12:46.711788	Blessings	Nyirenda	user
1	admin	admin@example.com	$2b$12$oBFBTZn9DHNspnyJyHDrZe55E.Dil7ixke6SVJrl4fMq.2PR1ipiO	2025-07-05 02:29:41.062875	2025-07-10 05:06:13.008799	\N	\N	user
\.


--
-- Name: predictions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.predictions_id_seq', 29, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: predictions predictions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: TABLE predictions; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.predictions FROM postgres;
GRANT ALL ON TABLE public.predictions TO postgres WITH GRANT OPTION;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.users FROM postgres;
GRANT ALL ON TABLE public.users TO postgres WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres REVOKE ALL ON TABLES FROM postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO postgres WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

